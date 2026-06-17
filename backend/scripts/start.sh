#!/bin/sh
# Wait for DB, create tables, then run the passed command (gunicorn/uvicorn).
set -e

echo "Initializing database..."
python -m app.db.init_db

echo "Starting: $*"
exec "$@"
