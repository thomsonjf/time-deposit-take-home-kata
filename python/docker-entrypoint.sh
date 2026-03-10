#!/bin/bash
set -e

echo "Starting Time Deposit API..."

# Wait for database to be ready
echo "Waiting for database..."
while ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" > /dev/null 2>&1; do
  sleep 1
done
echo "Database is ready"

# Start the application
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
