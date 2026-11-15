#!/bin/sh
# Azure App Service startup command: `sh startup.sh`
set -e
mkdir -p "${DATA_DIR:-.}"
python manage.py migrate --noinput
# S35: clear out reports closed more than 60 days ago (also runs when an admin opens Lost reports).
python manage.py delete_old_closed_reports || echo "Cleanup failed; the app starts anyway."
# 2 processes x 4 threads: 8 requests at once, so one person waiting on the mail server
# does not hold up everyone else.
exec gunicorn config.wsgi --bind="0.0.0.0:${PORT:-8000}" --workers 2 --threads 4 --worker-class gthread \
    --timeout 120 --access-logfile -
