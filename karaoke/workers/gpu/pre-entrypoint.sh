#!/bin/sh
set -e

echo "Running daemon..."

python /app/daemon/transcribe.py &

exec "$@"