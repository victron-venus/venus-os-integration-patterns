FROM python:3.14-slim@sha256:51dafde81dbdb6ebde285137a295cf18a47ca95234fe388a343719cb97305b3d

# Install system dependencies for D-Bus
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    dbus \
    gir1.2-glib-2.0 \
    libcairo2-dev \
    libdbus-1-dev \
    libgirepository-2.0-dev \
    libglib2.0-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt requirements-build.txt requirements-cairo.txt ./
RUN pip install --no-cache-dir --only-binary=:all: --require-hashes -r requirements-build.txt \
    && pip install --no-cache-dir --only-binary=:all: --no-binary=pycairo \
        --no-build-isolation --require-hashes -r requirements-cairo.txt \
    && pip install --no-cache-dir --only-binary=:all: --no-binary=dbus-python,pygobject,pycairo \
        --no-build-isolation --require-hashes -r requirements.txt

# Copy application
COPY src/ ./src/
# Verify host bindings before switching to the non-root runtime user.
RUN python -c "import src.mqtt_to_dbus" \
    && useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "-m", "src.mqtt_to_dbus"]
CMD ["-c", "/app/config.yaml"]
