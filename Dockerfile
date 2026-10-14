# ==============================================================================
# SkillMatch AI - Production Container Image
# Multi-stage / optimized lean Python 3.11 environment with security hardening
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PORT=8000 \
    ENVIRONMENT=production

# Install minimal OS dependencies for ML libraries and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root application user for container security
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Set working directory
WORKDIR /app

# Copy dependency definition first for optimal Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend ./backend
COPY frontend ./frontend
COPY sample_resumes ./sample_resumes
COPY gunicorn_conf.py .
COPY run.py .

# Ensure ownership by appuser
RUN chown -R appuser:appgroup /app

# Switch to unprivileged user
USER appuser

# Expose HTTP port
EXPOSE 8000

# Container health monitoring
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Production startup using Gunicorn process manager with Uvicorn workers
CMD ["gunicorn", "-c", "gunicorn_conf.py", "backend.main:app"]
