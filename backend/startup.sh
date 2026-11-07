#!/bin/sh
# Azure App Service startup command: `sh startup.sh`
set -e
mkdir -p "${DATA_DIR:-.}"
python manage.py migrate --noinput
python manage.py createcachetable
# 2 processes x 4 threads: 8 requests at once, so one person waiting on the mail server
# does not hold up everyone else.
exec gunicorn config.wsgi --bind="0.0.0.0:${PORT:-8000}" --workers 2 --threads 4 --worker-class gthread \
    --timeout 120 --access-logfile -
