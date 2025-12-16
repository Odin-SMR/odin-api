# Build stage for Node.js frontend
FROM node:22-bookworm-slim AS frontend-builder
COPY ./src/odinapi/static /odin/src/odinapi/static
COPY ./package*.json /odin/
COPY webpack.config.js /odin/
WORKDIR /odin
RUN npm ci --production=false
RUN npm run build

# Main application stage
FROM python:3.13-slim-bookworm
COPY requirements_python.apt /app/
WORKDIR /app

# Install system dependencies and clean up in a single layer
RUN set -x && \
    apt-get update && \
    xargs apt-get install -y --no-install-recommends < requirements_python.apt && \
    apt-get -y upgrade && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/odinapi /app/odinapi/
COPY --from=frontend-builder /odin/src/odinapi/static /app/odinapi/static

# Copy configuration files
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh
COPY gunicorn.conf.py /app/
COPY logconf.yaml /app/

# Pre-create certificate directory (will be populated by entrypoint)
RUN mkdir -p /root/.postgresql

# Add health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/rest_api/health_check', timeout=3)" || exit 1

ENTRYPOINT [ "/entrypoint.sh" ]
EXPOSE 8000
CMD ["gunicorn", "--config", "gunicorn.conf.py"]
