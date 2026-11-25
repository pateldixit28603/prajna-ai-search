# ---------- 1. build the React frontend ----------
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---------- 2. Python API that also serves the built UI ----------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=web /web/dist /app/frontend/dist
ENV DATA_DIR=/data
ENV PORT=8000
EXPOSE 8000
HEALTHCHECK CMD python -c "import os,urllib.request;urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",\"8000\")}/api/health')"
# Hosting platforms (Render, Railway, Fly, HF Spaces) inject $PORT
CMD ["sh", "-c", "mkdir -p \"$DATA_DIR\" && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips '*'"]
