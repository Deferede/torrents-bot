FROM python:3.12-alpine

WORKDIR /app

# Install build dependencies for ARM
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    && apk add --no-cache \
    curl

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy uv files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Clean up build dependencies
RUN apk del .build-deps

# Copy source code
COPY main.py .
COPY src/ src/

# Create non-root user for security
RUN adduser -D -s /bin/sh appuser
USER appuser

# Run the application
CMD ["uv", "run", "main.py"]
