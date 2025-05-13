#!/bin/bash

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis started"

# Run migrations with poetry
echo "Running database migrations..."
poetry run alembic upgrade head

# Start the application
echo "Starting application..."
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload