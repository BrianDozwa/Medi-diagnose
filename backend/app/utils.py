"""
Utility functions for image handling and preprocessing.

Includes:
- dicom_bytes_to_pil: Convert raw DICOM bytes to a PIL Image in RGB mode.
- preprocess_pil_image: Preprocess a PIL image into a batched torch.Tensor ready for DenseNet.
- tensor_to_base64_overlay: Create a base64 PNG data-URI overlaying a heatmap on the original image.

Notes on performance:
- Consider caching torchvision transforms if called repeatedly.
- Batch processing should be done upstream for throughput; this module processes a single image at a time.
- Preprocessing can be moved to the model's device later if that becomes a bottleneck.
"""

from __future__ import annotations

import base64
import io
from typing import Optional

import numpy as np
import pydicom
import torch
from PIL import Image
from torchvision import transforms


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def _min_max_scale_to_uint8(array: np.ndarray) -> np.ndarray:
    """Scale a numeric array to the uint8 range [0, 255].

    NaNs are treated as zeros after scaling. If the input has no variation,
    returns an array of zeros.
    """
    arr = np.asarray(array, dtype=np.float32)
    if arr.size == 0:
        return np.zeros_like(arr, dtype=np.uint8)

    finite_mask = np.isfinite(arr)
    if not finite_mask.any():
        return np.zeros(arr.shape, dtype=np.uint8)

    finite_vals = arr[finite_mask]
    min_val = float(finite_vals.min())
    max_val = float(finite_vals.max())
    range_val = max_val - min_val

    if range_val <= 0:
        scaled = np.zeros_like(arr, dtype=np.float32)
    else:
        scaled = (arr - min_val) / range_val
        scaled = np.clip(scaled, 0.0, 1.0)

    scaled[~finite_mask] = 0.0
    return (scaled * 255.0 + 0.5).astype(np.uint8)


def dicom_bytes_to_pil(dicom_bytes: bytes) -> Image.Image:
    """Convert DICOM bytes to a PIL Image in RGB mode.

    Steps:
    - Parse DICOM from bytes using pydicom.
    - Extract `pixel_array` and min-max rescale to 0..255.
    - Create a PIL Image in 'L' mode, handle MONOCHROME1 inversion, then convert to 'RGB'.

    Parameters
    ----------
    dicom_bytes: bytes
        Raw bytes of a DICOM file.

    Returns
    -------
    PIL.Image
        The converted image in RGB mode.
    """
    ds = pydicom.dcmread(io.BytesIO(dicom_bytes), force=True)

    # pydicom may need to decode pixel data; accessing pixel_array triggers it.
    pixel_data = ds.pixel_array  # type: ignore[attr-defined]
    pixel_uint8 = _min_max_scale_to_uint8(pixel_data)

    # Handle MONOCHROME1 (where 0 is white). Invert after scaling to uint8.
    photometric = getattr(ds, "PhotometricInterpretation", None)
    if isinstance(photometric, str) and photometric.upper() == "MONOCHROME1":
        pixel_uint8 = 255 - pixel_uint8

    # Ensure 2D grayscale; if 3D, reduce via first channel.
    if pixel_uint8.ndim == 3:
        pixel_uint8 = pixel_uint8[..., 0]

    pil_img = Image.fromarray(pixel_uint8, mode="L").convert("RGB")
    return pil_img


# Cache transforms for reuse across calls.
_PREPROCESS_TRANSFORMS = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ]
)


def preprocess_pil_image(pil_img: Image.Image) -> torch.Tensor:
    """Preprocess a PIL image for DenseNet-style inference.

    Pipeline:
    - Resize shortest side to 256
    - Center-crop to 224x224
    - Convert to tensor in [0,1]
    - Normalize with ImageNet mean/std

    Returns a CPU tensor with shape (1, 3, 224, 224).
    """
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")

    tensor_chw = _PREPROCESS_TRANSFORMS(pil_img)
    batched = tensor_chw.unsqueeze(0)
    return batched  # remain on CPU by design


def _rgba_heatmap_overlay(base_rgb: Image.Image, heatmap: np.ndarray, alpha_scale: float = 192.0) -> Image.Image:
    """Create an RGBA overlay from a heatmap and composite it onto `base_rgb`.

    The overlay is a red-tinted alpha layer where alpha is proportional to the
    heatmap intensity.

    Parameters
    ----------
    base_rgb: PIL.Image
        RGB image to serve as the background.
    heatmap: np.ndarray
        Heatmap normalized in [0, 1], shape (H, W) or (H, W, 1).
    alpha_scale: float
        Maximum alpha value (0..255). 192 gives a visible but not overpowering overlay.
    """
    if heatmap.ndim == 3:
        heatmap = heatmap[..., 0]

    heatmap = np.clip(heatmap.astype(np.float32), 0.0, 1.0)

    # Resize heatmap to base image size
    hm_uint8 = (heatmap * 255.0 + 0.5).astype(np.uint8)
    hm_img = Image.fromarray(hm_uint8, mode="L").resize(base_rgb.size, resample=Image.BILINEAR)

    # Build RGBA heatmap: red channel carries color, alpha proportional to heat
    r = Image.new("L", base_rgb.size, color=255)
    g = Image.new("L", base_rgb.size, color=0)
    b = Image.new("L", base_rgb.size, color=0)

    # Scale alpha by alpha_scale/255 to control intensity
    alpha = hm_img.point(lambda v: int(min(255, max(0, v * (alpha_scale / 255.0)))))

    heat_rgba = Image.merge("RGBA", (r, g, b, alpha))
    base_rgba = base_rgb.convert("RGBA")
    composited = Image.alpha_composite(base_rgba, heat_rgba)
    return composited


def tensor_to_base64_overlay(original_pil: Image.Image, heatmap_np: Optional[np.ndarray]) -> str:
    """Overlay a heatmap onto the original image and return a base64 PNG data URI.

    The heatmap is assumed to be normalized to [0, 1] with shape (H, W). It is
    resized to the original image's size, converted to a red transparency mask,
    and alpha-composited over the original.

    Returns an empty string if `heatmap_np` is None.
    """
    if heatmap_np is None:
        return ""

    if original_pil.mode != "RGB":
        base_rgb = original_pil.convert("RGB")
    else:
        base_rgb = original_pil

    overlay = _rgba_heatmap_overlay(base_rgb, heatmap_np)

    with io.BytesIO() as buffer:
        overlay.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}" 