FROM python:3.12-slim@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36

# Install system dependencies for D-Bus
RUN apt-get update && apt-get install -y --no-install-recommends \
    dbus \
    libdbus-1-dev \
    libglib2.0-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/

# Run as non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "-m", "src.mqtt_to_dbus"]
CMD ["-c", "/app/config.yaml"]