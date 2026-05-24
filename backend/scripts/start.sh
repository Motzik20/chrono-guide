#!/bin/bash
set -e

chmod +x "$0"

echo "Running database migrations..."
alembic upgrade head

echo "Starting API server..."
exec "$@"
