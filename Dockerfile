# ---- Etapa 1: build do frontend (Bun + Vite) ----
FROM oven/bun:1 AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/bun.lock ./
RUN bun install --frozen-lockfile
COPY frontend/ ./
RUN bun run build

# ---- Etapa 2: runtime do backend (FastAPI) ----
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY lightrag_pdf_otimizado/ ./lightrag_pdf_otimizado/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

EXPOSE 8001

CMD ["sh", "-c", "uvicorn backend.server:app --host 0.0.0.0 --port ${PORT:-8001}"]
