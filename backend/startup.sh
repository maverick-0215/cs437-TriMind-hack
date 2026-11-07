#!/bin/sh
# Azure App Service startup command: `sh startup.sh`
set -e
mkdir -p "${DATA_DIR:-.}"
python manage.py migrate --noinput
exec gunicorn config.wsgi --bind="0.0.0.0:${PORT:-8000}" --workers 2 --timeout 120 --access-logfile -
