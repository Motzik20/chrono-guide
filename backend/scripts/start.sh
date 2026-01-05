#!/bin/bash
set -e

chmod +x "$0"

echo "Running database migrations..."
poetry run alembic upgrade head

echo "Starting API server..."
exec "$@"