#!/usr/bin/env bash
# Railway build script — runs on every deploy before the service starts.
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate
