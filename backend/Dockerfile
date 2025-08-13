# Backend API Dockerfile
# If you want GPU support, use an nvidia/cuda base image and install torch with CUDA.
# Example: FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 and pip install torch==<version>+cu121

FROM python:3.10-slim

# Install system dependencies for Pillow and build tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libjpeg-dev \
       zlib1g-dev \
       libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend sources
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 