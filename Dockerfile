# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1 - builder: resolve and install dependencies into an isolated venv.
# Build tooling never reaches the final image.
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Dependency layer is cached independently from the source code:
# requirements.txt changes -> reinstall; app code changes -> cache hit.
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    # uvloop/httptools/watchfiles: production performance + --reload support.
    && pip install "uvicorn[standard]" \
    # zoneinfo needs an IANA database; Debian slim ships none.
    # app/scrapers/ice.py uses ZoneInfo("America/New_York").
    && pip install tzdata \
    && find /opt/venv -name '__pycache__' -type d -prune -exec rm -rf {} + \
    && find /opt/venv -name '*.pyc' -delete

# ---------------------------------------------------------------------------
# Stage 2 - runtime: slim image, no compilers, no pip cache, non-root user.
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Unprivileged user; no shell login, no home clutter.
RUN groupadd --system --gid 1001 appuser \
    && useradd --system --uid 1001 --gid appuser --no-create-home --shell /usr/sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser run.py ./

USER appuser

EXPOSE 8000

# Host/port come from the environment; no value is baked into the image.
# `exec` keeps uvicorn as PID 1 so SIGTERM reaches it (clean `docker stop`).
CMD ["sh", "-c", "exec uvicorn app.main:app --host ${APP_HOST:-0.0.0.0} --port ${APP_PORT:-8000}"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:' + os.getenv('APP_PORT', '8000') + '/health', timeout=4).status == 200 else 1)"
