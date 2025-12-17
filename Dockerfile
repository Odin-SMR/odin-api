# Main application stage
FROM python:3.13-slim-bookworm

# Install uv for fast, reliable dependency management (pinned version for reproducibility)
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

COPY requirements_python.apt /app/
WORKDIR /app

# Install system dependencies and clean up in a single layer
RUN set -x && \
    apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get -y upgrade && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies using uv (syncs from pyproject.toml)
COPY pyproject.toml uv.lock README.md /app/
RUN set -e && \
    uv sync --frozen --no-dev --no-install-project && \
    echo "Dependencies installed successfully"

# Copy application code (maintain src directory structure for uv_build)
COPY src/odinapi /app/src/odinapi/

# Copy configuration files
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh
COPY gunicorn.conf.py /app/
COPY logconf.yaml /app/

# Pre-create certificate directory (will be populated by entrypoint)
RUN mkdir -p /root/.postgresql

# Add health check (matches ECS task definition)
HEALTHCHECK --interval=120s --timeout=20s --start-period=40s --retries=5 \
    CMD curl -f http://localhost:8000/rest_api/health_check || exit 1

ENTRYPOINT [ "/entrypoint.sh" ]
EXPOSE 8000
CMD ["uv", "run", "--no-dev", "gunicorn", "--config", "gunicorn.conf.py"]
