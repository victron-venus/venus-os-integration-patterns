FROM python:3.14-slim@sha256:51dafde81dbdb6ebde285137a295cf18a47ca95234fe388a343719cb97305b3d

# Install system dependencies for D-Bus
RUN apt-get update && apt-get install -y --no-install-recommends \
    dbus \
    libdbus-1-dev \
    libglib2.0-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt requirements-build.txt ./
RUN pip install --no-cache-dir --only-binary=:all: --require-hashes -r requirements-build.txt && \
    pip install --no-cache-dir --no-build-isolation --require-hashes -r requirements.txt

# Copy application
COPY src/ ./src/

# Run as non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "-m", "src.mqtt_to_dbus"]
CMD ["-c", "/app/config.yaml"]