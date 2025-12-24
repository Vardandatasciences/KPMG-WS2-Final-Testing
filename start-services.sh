#!/bin/bash
set -e

# Start nginx in background
nginx -g "daemon off;" &
NGINX_PID=$!

# Start Django in background
python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

# Wait for either process to exit
wait $NGINX_PID $DJANGO_PID

