import numpy as np
import torch
from PIL import Image

from backend.app.utils import preprocess_pil_image


def test_preprocess_pil_image_shapes_and_dtype() -> None:
    # Create a simple 300x300 grayscale gradient pattern
    row = np.linspace(0, 255, 300, dtype=np.uint8)
    arr = np.tile(row, (300, 1))  # shape (300, 300)

    img = Image.fromarray(arr, mode="L")

    tensor = preprocess_pil_image(img)

    assert isinstance(tensor, torch.Tensor)
    assert tensor.dtype == torch.float32
    assert tuple(tensor.shape) == (1, 3, 224, 224)
    assert tensor.device.type == "cpu" 