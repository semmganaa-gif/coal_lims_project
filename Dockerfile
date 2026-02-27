# =============================================================================
# COAL LIMS - Production Dockerfile
# Multi-stage build: dependencies → compile → production
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn redis

# -----------------------------------------------------------------------------
# Stage 2: Compiler - Compile .py → .pyc, remove source
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS compiler

WORKDIR /app

# Copy application source code
COPY . .

# Compile all Python files to bytecode (.pyc)
# Then remove .py source files (keep only compiled .pyc)
# Keep: run.py (gunicorn entry), config.py (needs to be readable for debugging)
# Keep: migrations/ (Alembic needs .py files to run)
RUN python -m compileall -b -q app/ && \
    find app/ -name "*.py" -type f -delete && \
    python -m compileall -b -q run.py config.py && \
    rm -rf __pycache__ && \
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# -----------------------------------------------------------------------------
# Stage 3: Production - Minimal runtime image
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS production

# Labels
LABEL maintainer="LIMS Team"
LABEL version="1.0"
LABEL description="Coal LIMS - Laboratory Information Management System"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd -r lims && useradd -r -g lims lims

# Copy compiled application from compiler stage
COPY --from=compiler --chown=lims:lims /app .

# Create necessary directories
RUN mkdir -p instance logs backups app/static/uploads && \
    chown -R lims:lims instance logs backups app/static/uploads

# Environment variables
ENV FLASK_APP=run.py \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER lims

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run gunicorn
CMD ["gunicorn", \
    "--worker-class", "gthread", \
    "--workers", "4", \
    "--threads", "2", \
    "--bind", "0.0.0.0:5000", \
    "--timeout", "120", \
    "--keep-alive", "5", \
    "--max-requests", "1000", \
    "--max-requests-jitter", "50", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "run:app"]
