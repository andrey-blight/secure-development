# builder stage
FROM python:3.11-slim@sha256:e4676722fba839e2e5cdb844a52262b43e90e56dbd55b7ad953ee3615ad7534f AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# create venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --disable-pip-version-check --upgrade pip==24.2 && \
    pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

# runtime stage
FROM python:3.11-slim@sha256:e4676722fba839e2e5cdb844a52262b43e90e56dbd55b7ad953ee3615ad7534f

# metadata
LABEL maintainer="aakizhinov@edu.hse.ru" \
      version="0.1.0" \
      description="SecDev Course App - secure FastAPI application"

# install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# create non-privileged user
RUN groupadd -r app && \
    useradd -r -g app --home-dir=/app --shell=/sbin/nologin app

WORKDIR /app

# copy venv from builder stage
COPY --from=builder --chown=app:app /opt/venv /opt/venv

# copy app code
COPY --chown=app:app app ./app
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app alembic.ini .

# Copy and setup entrypoint script (before USER app)
COPY --chown=app:app docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# activate venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

USER app

EXPOSE 8000

HEALTHCHECK --interval=60s --timeout=1s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
