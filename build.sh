#!/usr/bin/env bash
# Railway build script — runs during image build (no database available here).
set -o errexit

export DJANGO_SETTINGS_MODULE=core.settings.prod

pip install -r requirements.txt

python manage.py collectstatic --no-input
