#!/bin/bash

set -e

cd d2qc

# Wait for database to reply
while ! nc -z db 5432; do
  sleep 1
  echo "Waiting for Postgresql"
done

if [ "$DJANGO_DEBUG" == "True" ]; then
  echo "Debugging"
  python manage.py migrate --no-input
  python manage.py collectstatic --no-input
  python manage.py runserver 0.0.0.0:8000
else
  echo "Production mode"
  python manage.py migrate --no-input
  python manage.py collectstatic --no-input

  exec "$@"
fi
