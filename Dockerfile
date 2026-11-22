FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# 1) Copy dependency files first and install third-party dependencies (layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# 2) Copy project source, scripts, and README (models are mounted at runtime)
COPY README.md ./
COPY src/ ./src/
COPY scripts/ ./scripts/
RUN mkdir -p /app/models

# 3) Install the project itself into the virtual environment
RUN uv sync --frozen --no-dev

ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5000
CMD ["flask", "--app", "secsai_group_6.backend.app", "run", "--host", "0.0.0.0", "--port", "5000"]
