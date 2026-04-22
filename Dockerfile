# -------- Stage 1: Build frontend --------
    FROM node:20-alpine AS frontend-builder

    WORKDIR /app/frontend
    
    # Install deps
    COPY frontend/package*.json ./
    RUN npm ci
    
    # Copy frontend
    COPY frontend/ .
    
    # Build static export
    RUN npm run build
    
    # -------- Stage 2: Backend --------
    FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
    
    WORKDIR /app
    
    ENV UV_COMPILE_BYTECODE=1 \
        UV_LINK_MODE=copy \
        PYTHONUNBUFFERED=1
    
    # Install backend deps
    COPY backend/pyproject.toml backend/uv.lock ./backend/
    WORKDIR /app/backend
    RUN uv sync --frozen --no-dev
    
    # Copy backend source
    COPY backend/ .
    
    # Copy frontend static output
    WORKDIR /app
    COPY --from=frontend-builder /app/frontend/out ./static
    
    EXPOSE 8000
    
    CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]