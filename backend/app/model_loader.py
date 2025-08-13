"""
Model loader utilities for CheXNet-style DenseNet-121 classifier.

Python 3.10+

This module exposes a single entry point:
    - get_model_and_device(model_path: str | None = None, force_cpu: bool = False)

Behavior:
- Detect device (CUDA if available and not forced to CPU; otherwise CPU).
- Build torchvision.models.densenet121 backbone.
- Replace its classifier with a Linear layer mapping to 14 classes.
- Optionally load a checkpoint into the model. If any tensor shapes mismatch,
  raise a clear RuntimeError that lists the offending keys and shapes.
- If no checkpoint, use ImageNet-pretrained backbone and initialize the new
  classifier weights with kaiming_normal_.
- Move to device, set eval() and return (model, device).

Notes:
- Put your real CheXNet weights at a path like:
    backend/model/chexnet_weights.pth
  and pass that path to the function.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import torch
import torch.nn as nn

try:
    # Prefer modern torchvision API (0.13+)
    from torchvision.models import densenet121, DenseNet121_Weights  # type: ignore
    _TORCHVISION_HAS_WEIGHTS_ENUM = True
except Exception:  # pragma: no cover - fallback for older torchvision
    from torchvision.models import densenet121  # type: ignore
    DenseNet121_Weights = None  # type: ignore
    _TORCHVISION_HAS_WEIGHTS_ENUM = False


NUM_CLASSES: int = 14


def _select_device(force_cpu: bool) -> torch.device:
    """Select a torch.device. Prefer CUDA if available and not forced to CPU."""
    if torch.cuda.is_available() and not force_cpu:
        device = torch.device("cuda")
        print("[model_loader] Using CUDA device")
    else:
        device = torch.device("cpu")
        print("[model_loader] Using CPU device")
    return device


def _build_densenet121_backbone() -> nn.Module:
    """Build a DenseNet-121 backbone, optionally with ImageNet weights.

    Returns the model with its original classifier still attached.
    """
    if _TORCHVISION_HAS_WEIGHTS_ENUM and DenseNet121_Weights is not None:
        print("[model_loader] Loading DenseNet-121 with ImageNet pretrained weights (weights enum)")
        model = densenet121(weights=DenseNet121_Weights.IMAGENET1K_V1)  # type: ignore[arg-type]
    else:
        # Fallback for older torchvision where "pretrained=True" is the flag
        print("[model_loader] Loading DenseNet-121 with ImageNet pretrained weights (pretrained=True)")
        model = densenet121(pretrained=True)  # type: ignore[call-arg]
    return model


def _replace_classifier(model: nn.Module, num_classes: int) -> None:
    """Replace the classifier (final linear layer) with the desired number of classes."""
    if not hasattr(model, "classifier"):
        raise AttributeError("DenseNet-121 model has no attribute 'classifier'. Unexpected torchvision version.")

    classifier: nn.Module = getattr(model, "classifier")
    if not isinstance(classifier, nn.Linear):
        raise TypeError(f"Expected model.classifier to be nn.Linear, got {type(classifier)!r}")

    in_features: int = classifier.in_features
    new_head = nn.Linear(in_features, num_classes)
    setattr(model, "classifier", new_head)


def _init_classifier_kaiming(model: nn.Module) -> None:
    """Initialize the new classifier head with kaiming_normal_ and zero bias."""
    linear = getattr(model, "classifier")
    if isinstance(linear, nn.Linear):
        nn.init.kaiming_normal_(linear.weight, nonlinearity="linear")
        if linear.bias is not None:
            nn.init.zeros_(linear.bias)
        print("[model_loader] Initialized classifier weights with kaiming_normal_ and zero bias")


def _extract_state_dict(checkpoint: object) -> Dict[str, torch.Tensor]:
    """Attempt to extract a state_dict from various checkpoint formats.

    Supported patterns:
    - checkpoint is already a state_dict (mapping of string -> tensor)
    - checkpoint has one of the common keys: 'state_dict', 'model_state_dict', 'model', 'weights', 'params'
    """
    if isinstance(checkpoint, dict):
        # Common container keys used during training
        for key in ("state_dict", "model_state_dict", "model", "weights", "params"):
            maybe = checkpoint.get(key)
            if isinstance(maybe, dict) and all(isinstance(k, str) for k in maybe.keys()):
                return maybe  # type: ignore[return-value]
        # Otherwise if it looks like a state_dict already
        if all(isinstance(k, str) for k in checkpoint.keys()):
            return checkpoint  # type: ignore[return-value]

    raise RuntimeError(
        "[model_loader] Could not extract a state_dict from checkpoint. "
        "Expected a dict with tensor values or a dict containing 'state_dict'/'model_state_dict'."
    )


def _strip_module_prefix(state_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    """Remove a leading 'module.' prefix (from DataParallel/DistributedDataParallel) if present."""
    fixed: Dict[str, torch.Tensor] = {}
    for k, v in state_dict.items():
        if k.startswith("module."):
            fixed[k[len("module."):]] = v
        else:
            fixed[k] = v
    return fixed


def _check_shape_compatibility(model: nn.Module, external_state: Dict[str, torch.Tensor]) -> None:
    """Raise a clear RuntimeError if any overlapping tensors have mismatched shapes."""
    model_state = model.state_dict()
    mismatches: list[tuple[str, torch.Size, torch.Size]] = []
    for k, ext_t in external_state.items():
        if k in model_state:
            model_t = model_state[k]
            if model_t.shape != ext_t.shape:
                mismatches.append((k, model_t.shape, ext_t.shape))
    if mismatches:
        details = "\n".join(
            f" - {k}: expected {exp} but found {got}" for k, exp, got in mismatches
        )
        raise RuntimeError(
            "[model_loader] Checkpoint tensor shape mismatches detected:\n" + details
        )


def get_model_and_device(model_path: str | None = None, force_cpu: bool = False) -> tuple[nn.Module, torch.device]:
    """Create a DenseNet-121 model configured for 14-class CheXNet-style inference.

    Parameters
    ----------
    model_path:
        Optional path to a weights checkpoint. If provided and the file exists,
        it will be loaded with map_location set to the selected device. If the
        checkpoint contains tensors with shapes that do not match the model,
        a RuntimeError will be raised with detailed information.
    force_cpu:
        If True, forces computation on CPU even if CUDA is available.

    Returns
    -------
    (model, device):
        The prepared torch.nn.Module (set to eval mode and moved to device) and
        the torch.device used.

    Examples
    --------
    Place your CheXNet weights at a path like 'backend/model/chexnet_weights.pth' and call:
        model, device = get_model_and_device("backend/model/chexnet_weights.pth")
    """
    device = _select_device(force_cpu=force_cpu)

    # Build backbone and attach our 14-class head
    model = _build_densenet121_backbone()
    _replace_classifier(model, NUM_CLASSES)

    ckpt_path = Path(model_path) if model_path else None
    if ckpt_path and ckpt_path.is_file():
        print(f"[model_loader] Loading checkpoint from '{ckpt_path.as_posix()}' (map_location={device})")
        # Important: ensure model is on the intended device before loading
        model.to(device)

        checkpoint = torch.load(ckpt_path.as_posix(), map_location=device)
        state_dict = _extract_state_dict(checkpoint)
        state_dict = _strip_module_prefix(state_dict)

        # Validate shapes before actual load for clearer errors
        _check_shape_compatibility(model, state_dict)

        incompat = model.load_state_dict(state_dict, strict=False)
        if incompat.missing_keys:
            print("[model_loader] Warning: Missing keys in checkpoint (not loaded):")
            for k in incompat.missing_keys:
                print(f"  - {k}")
        if incompat.unexpected_keys:
            print("[model_loader] Warning: Unexpected keys in checkpoint (ignored):")
            for k in incompat.unexpected_keys:
                print(f"  - {k}")

        print("[model_loader] Checkpoint loaded successfully.")
    else:
        print("[model_loader] No checkpoint provided or file not found.")
        print("[model_loader] Using ImageNet-pretrained backbone and initializing new classifier.")
        _init_classifier_kaiming(model)
        model.to(device)

    model.eval()
    print("[model_loader] Model moved to device and set to eval() mode.")
    return model, device 