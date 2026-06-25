web: DJANGO_SETTINGS_MODULE=core.settings.prod python manage.py migrate --no-input && daphne -b 0.0.0.0 -p $PORT core.asgi:application
