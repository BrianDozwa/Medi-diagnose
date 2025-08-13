import io
from typing import Any, Dict

import numpy as np
import torch
from starlette.testclient import TestClient
from PIL import Image

from backend.app.main import app


class _DummyModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        # produce deterministic logits
        base = torch.linspace(-1.0, 1.0, steps=14).reshape(1, 14)
        self.register_buffer("_logits", base)

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # type: ignore[override]
        batch = x.shape[0]
        return self._logits.repeat(batch, 1)


def _make_test_jpeg_bytes() -> bytes:
    # simple RGB gradient image
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[..., 0] = np.linspace(0, 255, 64, dtype=np.uint8)[None, :]
    arr[..., 1] = np.linspace(255, 0, 64, dtype=np.uint8)[:, None]
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_predict_endpoint_with_dummy_model(monkeypatch: Any) -> None:
    # Substitute the real model with our dummy and ensure CPU device
    app.state.model = _DummyModel()
    app.state.device = torch.device("cpu")

    client = TestClient(app)

    jpg_bytes = _make_test_jpeg_bytes()
    files = {"file": ("test.jpg", jpg_bytes, "image/jpeg")}

    resp = client.post("/predict", files=files)
    assert resp.status_code == 200
    data: Dict[str, Any] = resp.json()
    assert "predictions" in data
    preds = data["predictions"]
    assert isinstance(preds, list)
    assert len(preds) == 14

    for item in preds:
        assert "label" in item and "probability" in item
        p = float(item["probability"])
        assert 0.0 <= p <= 1.0 