FROM python:3.11-slim

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Configurar uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copiar archivos de dependencias
COPY pyproject.toml uv.lock ./
COPY README.md ./

# Instalar dependencias en el sistema (sin el entorno virtual)
RUN uv sync --frozen --no-dev --no-install-project

# Copiar el código fuente y los tests (por si acaso)
COPY src ./src

# Instalar el proyecto en sí
RUN uv sync --frozen --no-dev

# Exponer el puerto de FastAPI
EXPOSE 8000

# Comando por defecto (usa el venv creado por uv)
CMD ["uv", "run", "uvicorn", "superstore_forecasting.api.main:app", "--host", "0.0.0.0", "--port", "8000"]