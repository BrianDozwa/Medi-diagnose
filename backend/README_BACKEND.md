# Backend API (FastAPI + PyTorch)

## Setup

- Python (local):
  - Create venv (recommended):
    - Windows (PowerShell): `python -m venv .venv; .venv\Scripts\Activate.ps1`
    - macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate`
  - Install deps:
    - `pip install -r backend/requirements.txt`
  - Configure env (optional):
    - Copy `backend/.env.example` to `backend/.env` and adjust values (e.g., `MODEL_PATH`).
  - Run API:
    - `cd backend && ./start.sh`

- Docker:
  - Build: `docker build -t chexnet-api ./backend`
  - Run: `docker run --rm -p 8000:8000 --env-file backend/.env chexnet-api`
  - GPU hint: If you need CUDA, use an `nvidia/cuda` base image in `Dockerfile` and install a CUDA-enabled `torch`.

## Environment

- `MODEL_PATH` (default resolves to `backend/model/chexnet_weights.pth` relative to the backend folder): path to weights. If missing, the server uses ImageNet backbone + randomly initialized classifier.
- `ALLOWED_ORIGINS` (default `*`)
- `API_PORT` (default `8000`)

## Test with curl

- Predict (DICOM):
```sh
curl -X POST -F "file=@/path/to/xray.dcm" http://localhost:8000/predict
```

- Predict with Grad-CAM (JPEG/PNG) targeting class index 3:
```sh
curl -X POST -F "file=@/path/to/xray.jpg" -F "target_class=3" http://localhost:8000/predict_cam
```

The `/predict` response returns all 14 labels with probabilities sorted descending.
The `/predict_cam` response additionally includes a `cam` field with a base64 PNG data URI if Grad-CAM succeeded. 

### DenseNet-121 model path: create and set

- Default path is now robust: resolves to `backend/model/chexnet_weights.pth` relative to the backend folder.
- You can override with `MODEL_PATH` env var.

### How to set it
- Option A (recommended): create `backend/.env`
  ```
  MODEL_PATH=./model/chexnet_weights.pth
  ```
  Then start with the provided script from `backend/`:
  ```
  ./start.sh
  ```

- Option B: pass env inline
  - PowerShell (from repo root):
    ```
    $env:MODEL_PATH="backend/model/chexnet_weights.pth"; uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
    ```

- Place your weights file at: `backend/model/chexnet_weights.pth`

Tests are still green after this change. 