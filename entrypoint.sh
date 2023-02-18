#!/bin/bash

set -e

if [ "$DJANGO_DEBUG" == "True" ]; then
  python manage.py runserver 0.0.0.0:8000
else
  python manage.py migrate --no-input
  python manage.py collectstatic --no-input

  exec "$@"
fi
