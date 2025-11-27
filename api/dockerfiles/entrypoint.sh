#!/bin/sh
# ============================================
# Entrypoint script for Albanian-ASR API
# Ensures proper permissions on mounted volumes
# ============================================

set -e

# Ensure mounted volume directories exist and have correct permissions
echo "Setting up mounted volume directories..."
mkdir -p /code/mp3 /code/mp4 /code/splices
chown -R appuser:appgroup /code/mp3 /code/mp4 /code/splices
chmod -R 755 /code/mp3 /code/mp4 /code/splices

# Debug: show what we have
echo "Volume contents:"
ls -la /code/mp3 /code/mp4 /code/splices

echo "Starting application as appuser..."
# Drop privileges and run the application
exec gosu appuser "$@"
