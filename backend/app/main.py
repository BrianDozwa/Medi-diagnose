"""
FastAPI application exposing prediction and Grad-CAM endpoints.

Environment variables:
- ALLOWED_ORIGINS: Comma-separated list of origins for CORS. Default: "*".
- MODEL_PATH: Path to a .pth checkpoint. Default: "./model/chexnet_weights.pth".

Notes:
- Place your real CheXNet weights at MODEL_PATH (e.g., ./model/chexnet_weights.pth).
- To enable GPU in containers, use a CUDA-enabled base image and run with
  --gpus all (Docker) or appropriate Kubernetes runtimeClass and resource requests.
"""
from __future__ import annotations

import os
from io import BytesIO
from typing import Any, List, Optional

import numpy as np
import torch
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pathlib import Path

from .model_loader import get_model_and_device
from .utils import dicom_bytes_to_pil, preprocess_pil_image, tensor_to_base64_overlay
from .cam import GradCAM


# 14-class CheXNet labels (NIH ChestX-ray14)
CHEXNET_LABELS: List[str] = [
    "Atelectasis",
    "Cardiomegaly",
    "Effusion",
    "Infiltration",
    "Mass",
    "Nodule",
    "Pneumonia",
    "Pneumothorax",
    "Consolidation",
    "Edema",
    "Emphysema",
    "Fibrosis",
    "Pleural_Thickening",
    "Hernia",
]


ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
# Default to backend/model/chexnet_weights.pth relative to this file, unless overridden
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_MODEL_PATH = (_BACKEND_ROOT / "model" / "chexnet_weights.pth").as_posix()
MODEL_PATH = os.getenv("MODEL_PATH", _DEFAULT_MODEL_PATH)

app = FastAPI(title="CheXNet Inference API", version="1.0.0")


# CORS configuration
if ALLOWED_ORIGINS.strip() == "*":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    origins = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
def _on_startup() -> None:
    model, device = get_model_and_device(MODEL_PATH)
    app.state.model = model
    app.state.device = device
    print(f"[api] Model loaded. Device: {device}")


@app.get("/health")
def health() -> dict[str, Any]:
    device: torch.device = getattr(app.state, "device", torch.device("cpu"))
    return {"status": "ok", "device": str(device)}


def _is_dicom(upload: UploadFile) -> bool:
    name = (upload.filename or "").lower()
    ctype = (upload.content_type or "").lower()
    return name.endswith(".dcm") or ("dicom" in ctype)


def _read_image_from_upload(upload: UploadFile) -> Image.Image:
    try:
        file_bytes = upload.file.read()
        if not file_bytes:
            raise ValueError("empty file")

        if _is_dicom(upload):
            pil_img = dicom_bytes_to_pil(file_bytes)
        else:
            pil_img = Image.open(BytesIO(file_bytes)).convert("RGB")
        return pil_img
    except Exception as e:  # noqa: BLE001 - return clean 400
        raise HTTPException(status_code=400, detail=f"Invalid image/DICOM: {e}")


@app.post("/predict")
def predict(file: UploadFile = File(...)) -> dict[str, Any]:
    try:
        pil_img = _read_image_from_upload(file)
        x = preprocess_pil_image(pil_img)  # (1,3,224,224) on CPU
        device: torch.device = app.state.device
        model: torch.nn.Module = app.state.model
        x = x.to(device)

        with torch.no_grad():
            logits = model(x)  # (1, 14)
            probs = torch.sigmoid(logits)[0].detach().cpu().numpy()

        probs_list = probs.tolist()
        preds = [
            {"label": label, "probability": float(prob)}
            for label, prob in zip(CHEXNET_LABELS, probs_list)
        ]
        preds_sorted = sorted(preds, key=lambda d: d["probability"], reverse=True)
        return {"predictions": preds_sorted}
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")


@app.post("/predict_cam")
def predict_cam(
    file: UploadFile = File(...),
    target_class: Optional[int] = Form(None),
) -> dict[str, Any]:
    try:
        pil_img = _read_image_from_upload(file)
        x_cpu = preprocess_pil_image(pil_img)  # CPU tensor
        device: torch.device = app.state.device
        model: torch.nn.Module = app.state.model

        x = x_cpu.to(device)
        with torch.no_grad():
            logits = model(x)
            probs = torch.sigmoid(logits)[0].detach().cpu().numpy()
        probs_list = probs.tolist()

        preds = [
            {"label": label, "probability": float(prob)}
            for label, prob in zip(CHEXNET_LABELS, probs_list)
        ]
        preds_sorted = sorted(preds, key=lambda d: d["probability"], reverse=True)

        # Determine target class: provided or top-1
        if target_class is None:
            target_class = int(np.argmax(probs))
        else:
            if not (0 <= int(target_class) < len(CHEXNET_LABELS)):
                raise HTTPException(status_code=400, detail="target_class out of range [0, 13]")

        # Compute Grad-CAM
        cam = GradCAM(model)
        heatmap = cam.get_cam(x, target_class=int(target_class))
        if heatmap is not None:
            cam_data_uri = tensor_to_base64_overlay(pil_img, heatmap)
        else:
            cam_data_uri = None

        return {"predictions": preds_sorted, "cam": cam_data_uri}

    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Predict+CAM failed: {e}")


if __name__ == "__main__":
    import uvicorn

    # Note: In production, prefer `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)  # nosec B104 