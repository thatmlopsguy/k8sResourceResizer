# syntax=docker/dockerfile:1

ARG TARGETPLATFORM=linux/amd64
ARG PYTHON_VERSION=3.13-slim
FROM --platform=$TARGETPLATFORM python:$PYTHON_VERSION AS builder

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app:/app/src" \
    DEBIAN_FRONTEND=noninteractive \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install system dependencies
RUN apt-get update \
    && apt-get upgrade -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl \
        git \
        pkg-config \
        gcc \
        g++ \
        libopenblas-dev \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install project dependencies from lockfile (without the project itself)
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY src ./src/

# Install the project itself
RUN uv sync --frozen --no-dev

# Create TEMP directory with proper permissions
RUN mkdir -p /app/tmp && chmod 777 /app/tmp

# Install kind, kubectl, and argocd
COPY docker/install.sh /install.sh
RUN chmod +x /install.sh && /install.sh

# Update and upgrade all packages
RUN apt-get update && apt-get upgrade -y

# Final stage
FROM --platform=$TARGETPLATFORM python:$PYTHON_VERSION

ENV TZ=Etc/UTC \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/app/.venv/bin:$PATH"

# Install minimal required packages
RUN set -eux; \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        openssl \
        curl \
        bash \
        tzdata \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/

RUN mkdir -p /app/tmp && chmod 777 /app/tmp

# Copy the virtual environment and source from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/pyproject.toml /app/

# Copy tools from builder stage
COPY --from=builder /usr/local/bin/kind /usr/local/bin/
COPY --from=builder /usr/local/bin/kubectl /usr/local/bin/
COPY --from=builder /usr/local/bin/argocd /usr/local/bin/
COPY --from=docker:dind@sha256:e0b121dfc337c0f5a9703ef0914a392864bde6db811f2ba5bdd617a6e932073e /usr/local/bin/ /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
