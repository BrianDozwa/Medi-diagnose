"""
Compact Grad-CAM implementation compatible with torchvision DenseNet-121.

- Automatically detects a good last conv layer under model.features if not provided.
- Computes Grad-CAM heatmaps for a given input tensor and optional target class.
- Provides a simple PIL overlay utility similar to utils.tensor_to_base64_overlay.

Python 3.10+
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

# Reuse overlay behavior from utils without re-encoding to base64
try:
    from .utils import _rgba_heatmap_overlay  # type: ignore
except Exception:  # pragma: no cover - allow standalone usage if utils not present
    _rgba_heatmap_overlay = None  # type: ignore


class GradCAM:
    """Grad-CAM for CNN classifiers (Designed for torchvision DenseNet-121).

    Parameters
    ----------
    model : torch.nn.Module
        The model to explain. Must output logits of shape (N, C).
    target_layer : str | None
        Dotted path to the conv layer to target. If None, the last Conv2d under
        `model.features` is used.
    """

    def __init__(self, model: nn.Module, target_layer: str | None = None) -> None:
        self.model = model.eval()
        self.model_requires_grad = True  # explicitly use autograd even in eval

        self._target_module: nn.Module | None = None
        self._target_module_name: str | None = None

        if target_layer is not None:
            module = self._get_module_by_name(self.model, target_layer)
            if module is None:
                raise ValueError(f"Target layer '{target_layer}' not found in model")
            self._target_module = module
            self._target_module_name = target_layer
        else:
            self._auto_select_target_layer()
            if self._target_module is None:
                raise ValueError("Could not automatically find a suitable target conv layer")

        # Buffers for captured tensors
        self._activations: Optional[torch.Tensor] = None
        self._gradients: Optional[torch.Tensor] = None

    # -------------------------
    # Public API
    # -------------------------
    def get_cam(self, input_tensor: torch.Tensor, target_class: int | None = None) -> Optional[np.ndarray]:
        """Compute Grad-CAM heatmap for a single input.

        Parameters
        ----------
        input_tensor : torch.Tensor
            Shape (1, 3, H, W). Should be normalized (ImageNet) and on CPU or the
            same device as the model. Grad-CAM is typically computed on CPU for
            simplicity, but CUDA works too.
        target_class : int | None
            Class index to target. If None, uses argmax of model logits.

        Returns
        -------
        Optional[np.ndarray]
            Heatmap in [0, 1] with shape (H', W') where H', W' are the spatial
            dimensions of the target layer activations, upsampled behavior is not
            included here. Returns None if gradients were not captured.
        """
        if self._target_module is None:
            print("[GradCAM] No target layer set; aborting.")
            return None

        self._clear_captures()

        # Register a forward hook on the target module to capture activations and their gradients
        def fwd_hook(_module: nn.Module, _inputs: tuple[torch.Tensor, ...], output: torch.Tensor) -> None:  # type: ignore[override]
            # Save feature maps and attach a grad hook to capture dL/dA (per sample)
            self._activations = output

            def grad_hook(grad: torch.Tensor) -> None:
                self._gradients = grad

            output.register_hook(grad_hook)

        hook_handle = self._target_module.register_forward_hook(fwd_hook)

        # Forward pass
        with torch.enable_grad():
            logits = self.model(input_tensor)

        # Decide target class
        if target_class is None:
            target_class = int(torch.argmax(logits, dim=1).item())

        # Backward for the selected class
        self.model.zero_grad(set_to_none=True)
        # Use sum over batch to support (potentially) larger batches; assumed 1 here
        selected = logits[:, target_class].sum()
        selected.backward(retain_graph=False)

        # Remove hook to avoid leaks
        try:
            hook_handle.remove()
        except Exception:
            pass

        if self._activations is None or self._gradients is None:
            print("[GradCAM] Gradients/activations were not captured. Ensure the target layer is correct.")
            return None

        # Expect shapes: activations (N, C, H, W), gradients (N, C, H, W)
        acts = self._activations
        grads = self._gradients
        if acts.dim() != 4 or grads.dim() != 4:
            print(f"[GradCAM] Unexpected tensor dims. activations: {acts.shape}, gradients: {grads.shape}")
            return None

        # Use batch index 0
        acts = acts[0]
        grads = grads[0]
        # Global average pooling on gradients -> weights per channel
        weights = torch.mean(grads, dim=(1, 2))  # (C,)
        # Weighted sum of activations
        cam = torch.sum(weights[:, None, None] * acts, dim=0)  # (H, W)
        cam = torch.relu(cam)

        # Normalize to [0, 1]
        if torch.isfinite(cam).all() and cam.max() > 0:
            cam = cam / (cam.max() + 1e-12)
        else:
            cam = torch.zeros_like(cam)

        heatmap = cam.detach().cpu().numpy().astype(np.float32)
        return heatmap

    def overlay(self, pil_img: Image.Image, heatmap_np: np.ndarray) -> Image.Image:
        """Overlay a Grad-CAM heatmap onto the original image and return a PIL image.

        If utils._rgba_heatmap_overlay is available, reuse it; otherwise, perform
        a simple red alpha overlay.
        """
        if heatmap_np is None:
            return pil_img

        if _rgba_heatmap_overlay is not None:
            return _rgba_heatmap_overlay(pil_img.convert("RGB"), heatmap_np)

        # Fallback minimal overlay without utils: red-tinted alpha mask
        hm = np.clip(heatmap_np.astype(np.float32), 0.0, 1.0)
        from PIL import Image as _Image  # local import to keep top minimal

        hm_uint8 = (hm * 255.0 + 0.5).astype(np.uint8)
        hm_img = _Image.fromarray(hm_uint8, mode="L").resize(pil_img.size, resample=_Image.BILINEAR)

        r = _Image.new("L", pil_img.size, color=255)
        g = _Image.new("L", pil_img.size, color=0)
        b = _Image.new("L", pil_img.size, color=0)
        alpha = hm_img.point(lambda v: int(min(255, max(0, v * (192.0 / 255.0)))))

        heat_rgba = _Image.merge("RGBA", (r, g, b, alpha))
        base_rgba = pil_img.convert("RGBA")
        return _Image.alpha_composite(base_rgba, heat_rgba)

    # -------------------------
    # Internals
    # -------------------------
    def _get_module_by_name(self, root: nn.Module, name: str) -> Optional[nn.Module]:
        current: nn.Module = root
        for part in name.split("."):
            if not hasattr(current, part):
                return None
            current = getattr(current, part)
        return current

    def _auto_select_target_layer(self) -> None:
        """Pick the last Conv2d module under model.features; fallback to any last Conv2d."""
        features = getattr(self.model, "features", None)
        candidates: list[tuple[str, nn.Module]] = []
        if isinstance(features, nn.Module):
            for name, module in features.named_modules():
                if isinstance(module, nn.Conv2d):
                    candidates.append((f"features.{name}", module))
        if not candidates:
            for name, module in self.model.named_modules():
                if isinstance(module, nn.Conv2d):
                    candidates.append((name, module))
        if candidates:
            self._target_module_name, self._target_module = candidates[-1]
            print(f"[GradCAM] Auto-selected target layer: {self._target_module_name}")
        else:
            self._target_module_name, self._target_module = None, None

    def _clear_captures(self) -> None:
        self._activations = None
        self._gradients = None


if __name__ == "__main__":  # pragma: no cover - simple sanity test
    import torchvision

    # Build a sample DenseNet-121 and test Grad-CAM shape
    try:
        model = torchvision.models.densenet121(weights=None)
    except TypeError:
        model = torchvision.models.densenet121(pretrained=False)  # older torchvision fallback

    cam = GradCAM(model)
    x = torch.randn(1, 3, 224, 224)
    heatmap = cam.get_cam(x)
    if heatmap is None:
        print("[GradCAM] Failed to compute heatmap.")
    else:
        print(f"[GradCAM] Heatmap shape: {heatmap.shape}, range: ({np.min(heatmap):.3f}, {np.max(heatmap):.3f})") 