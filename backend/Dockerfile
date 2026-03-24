# ── Stage 1: install Python deps ─────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first (saves ~1.5 GB vs CUDA build)
RUN pip install --no-cache-dir \
    torch==2.3.1 \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2: bake the sentence-transformer model into the image ───────────────
# Eliminates the slow network download on every cold start
FROM builder AS model-cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# ── Stage 3: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=model-cache /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=model-cache /usr/local/bin /usr/local/bin
# Copy cached model weights from builder's home
COPY --from=model-cache /root/.cache /root/.cache

COPY . .

# Cloud Run injects PORT; default to 8000 for local docker run
ENV PORT=8000
ENV DEMO_MODE=true
ENV DATABASE_URL=sqlite+aiosqlite:///./movies.db

# create_all() runs at startup — no migration step needed
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1
