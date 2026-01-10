#!/bin/bash

set -e  # Exit on any error

cd /django/app || exit 1

# Wait for PostgreSQL if USE_POSTGRES is set
if [ "${USE_POSTGRES:-False}" = "True" ]; then
    echo "Waiting for PostgreSQL to be ready..."
    python manage.py wait_for_postgres
fi

echo "Running migrations..."
python manage.py migrate

echo "Starting Django development server on 0.0.0.0:8000..."
python manage.py runserver 0.0.0.0:8000
