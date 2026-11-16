FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

# 2) Then the source.
COPY src ./src
COPY scripts ./scripts
RUN uv sync --locked --no-dev
RUN uv sync --frozen --no-install-project

COPY src/ ./src/
# Might have to change this since I don't have model on my system and I don't know where it is lol
COPY models/ ./models/
COPY README.md ./

RUN uv sync --frozen

ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"
