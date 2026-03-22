# ─────────────────────────────────────────────────────────────────────
# HireIQ Backend — Multi-stage Docker Build
# ─────────────────────────────────────────────────────────────────────
# Stage 1: Builder — install Python dependencies
# Stage 2: Runtime — slim image with only runtime deps
# ─────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ──────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build-time system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ──────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime system dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos "" hireiq && \
    chown -R hireiq:hireiq /app

USER hireiq

EXPOSE 8000

# Run with uvicorn — 4 workers for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
