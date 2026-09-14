

FROM python:3.13-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install "setuptools>=78.1.1" && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

    
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        curl libpq5 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
RUN python -m pip uninstall -y pip

COPY backend/ .

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD curl -fs http://localhost:8000/health/ || exit 1

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]


