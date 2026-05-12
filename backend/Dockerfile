# WebForge backend - multi-stage image ready for Render / Railway / Fly.io
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers \
    DEBIAN_FRONTEND=noninteractive

# System deps: playwright-chromium runtime, skillui (via node), taste-skill (via npx)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates gnupg \
        libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
        libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
        libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
        libatspi2.0-0 libwayland-client0 \
        fonts-liberation fonts-noto-color-emoji \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# skillui (required) — taste-skill is invoked lazily via npx
RUN npm install -g skillui || echo "skillui install skipped"

WORKDIR /app

# Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Playwright chromium
RUN python -m playwright install --with-deps chromium

# App code
COPY . /app
RUN mkdir -p /app/artifacts /app/uploads

ENV WEBFORGE_ARTIFACTS_DIR=/app/artifacts \
    WEBFORGE_UPLOADS_DIR=/app/uploads

EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
