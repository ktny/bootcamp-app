FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/usr/local

WORKDIR /app

COPY pyproject.toml uv.lock .
RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-cache --group dev --no-install-project

COPY . .

EXPOSE 8000
