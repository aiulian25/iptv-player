FROM python:3.11-slim
ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser -g 1000 && \
    useradd -r -u 1000 -g appuser -m -s /bin/bash appuser

# Copy and install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application source
COPY . /app

# Create runtime directories and chown to appuser
RUN mkdir -p /app/data /app/data/playlists /app/data/epg /app/data/sessions /app/config && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

ENV PORT=5000 PYTHONUNBUFFERED=1 PYTHONPATH=/app
EXPOSE 5000
CMD ["python", "-u", "backend/app.py"]
