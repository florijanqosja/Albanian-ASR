#!/bin/sh
# ============================================
# Entrypoint script for Albanian-ASR API
# Ensures proper permissions on mounted volumes
# ============================================

set -e

# Fix permissions on mounted volumes (runs as root initially)
echo "Setting permissions on mounted volumes..."
chown -R appuser:appgroup /code/mp3 /code/mp4 /code/splices 2>/dev/null || true
chmod -R 755 /code/mp3 /code/mp4 /code/splices 2>/dev/null || true

echo "Starting application as appuser..."
# Drop privileges and run the application
exec gosu appuser "$@"
