# SignVista backend image.
# Build from the repository root (the ISL models live outside backend/):
#   docker build -f backend/Dockerfile -t signvista-backend .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TF_CPP_MIN_LOG_LEVEL=2

# Runtime libraries for OpenCV / MediaPipe
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# Application code and models (paths mirror the repo layout)
COPY backend/app ./app
COPY backend/ml ./ml
COPY backend/config ./config
COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
COPY backend/static ./static
COPY ISL-Unified-Project/models /app/ISL-Unified-Project/models
COPY ISL-Unified-Project/config /app/ISL-Unified-Project/config

# Run as an unprivileged user; the SQLite database lives on a volume
RUN useradd --create-home --uid 1000 signvista \
    && mkdir -p /data \
    && chown -R signvista:signvista /data /app/backend/static
USER signvista

ENV DATABASE_URL=sqlite:////data/signvista.db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
