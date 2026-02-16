#!/bin/bash
set -e

# Wait for database
echo "Waiting for database..."
while ! nc -z $DB_HOST $DB_PORT; do
    sleep 0.1
done
echo "Database is ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start server
exec "$@"
