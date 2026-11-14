# ==========================================
# TradeSense AI — Cloud Run Production Image
# Multi-stage build for minimal attack surface
# ==========================================

# Stage 1: Build & Dependencies
FROM python:3.9-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final Production Runner
FROM python:3.9-slim AS runner

WORKDIR /app

# Non-root user for Google Cloud Run security compliance
RUN groupadd -r tradesense && useradd -r -g tradesense appuser

# Copy installed Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application source code and historical data
COPY app ./app
COPY ../data ./data

# Set environment paths
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    APP_ENV=production

# Grant permissions to non-root user
RUN chown -R appuser:tradesense /app /home/appuser
USER appuser

EXPOSE 8080

# Cloud Run dynamic PORT binding
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 2"]
