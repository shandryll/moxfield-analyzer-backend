# =============================================================================
# Multi-stage Dockerfile for Moxfield Analyzer
# Optimized for cloud deployment (Render, Fly.io, Railway, AWS, etc.)
#
# Usage:
#   Production: docker build -t moxfield-analyzer .
#   Dev:        docker build --target dev -t moxfield-analyzer:dev .
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Resolve and cache dependencies only
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy only dependency manifests (source not needed for dependency resolution)
COPY pyproject.toml uv.lock ./

# Install dependencies using lock file for reproducible builds
RUN uv sync --no-dev --frozen

# -----------------------------------------------------------------------------
# Stage 2: Base - Shared runtime setup for all environments
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS base

# Install system dependencies required by Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    fonts-liberation \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

WORKDIR /app

# Copy Python dependencies from builder virtual environment
COPY --from=builder /app/.venv/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app/.venv/bin/* /usr/local/bin/

# Copy application source code and metadata
COPY --chown=appuser:appuser pyproject.toml ./
COPY --chown=appuser:appuser src/ src/

# Install Playwright browsers as non-root user
# System dependencies already installed above — --with-deps NOT needed
USER appuser
ENV PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright
RUN python3 -m playwright install chromium

EXPOSE 3000

ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    WEB_CONCURRENCY=2

# -----------------------------------------------------------------------------
# Stage 3: Dev - Hot reload for local development
# Use: docker build --target dev -t moxfield-analyzer:dev .
# -----------------------------------------------------------------------------
FROM base AS dev

ENV ENVIRONMENT=development \
    LOG_LEVEL=DEBUG

CMD ["python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000", "--reload"]

# -----------------------------------------------------------------------------
# Stage 4: Production - Optimized for deployment (default target)
# -----------------------------------------------------------------------------
FROM base AS production

CMD ["sh", "-c", "python3 -m uvicorn src.main:app --host 0.0.0.0 --port 3000 --workers ${WEB_CONCURRENCY:-2}"]
