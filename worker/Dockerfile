FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock .python-version README.md ./
COPY src/ ./src/

RUN uv sync --frozen --no-dev

COPY models/ ./models/
COPY worker/ ./worker/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["uv", "run", "--no-sync", "python", "-m", "worker.main"]