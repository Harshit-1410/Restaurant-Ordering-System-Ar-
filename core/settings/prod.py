"""
Production settings for Railway deployment.

Required Railway environment variables:
  DJANGO_SETTINGS_MODULE = core.settings.prod
  SECRET_KEY              = <generated>
  ALLOWED_HOSTS           = yourdomain.up.railway.app
  DATABASE_URL            = <auto-injected by Railway PostgreSQL plugin>
  REDIS_URL               = <auto-injected by Railway Redis plugin>
  CLOUDINARY_URL          = cloudinary://api_key:api_secret@cloud_name
"""

import os as _os

import dj_database_url
from decouple import Csv, config

from .base import *  # noqa: F401, F403

DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Railway injects DATABASE_URL from the PostgreSQL plugin automatically
DATABASES = {
    'default': dj_database_url.config(
        env='DATABASE_URL',
        conn_max_age=600,
        ssl_require=True,
    )
}

# Railway injects REDIS_URL from the Redis plugin automatically.
# Override the base CHANNEL_LAYERS to use that URL directly.
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [config('REDIS_URL')],
        },
    },
}

# Cloudinary — persistent media storage for AR models and food images.
# dev.py uses local MEDIA_ROOT; prod uses Cloudinary so files survive redeploys.
# CLOUDINARY_URL is optional: if not set, media falls back to local MEDIA_ROOT.
_cloudinary_url = config('CLOUDINARY_URL', default='')

if _cloudinary_url:
    # Pop from os.environ BEFORE importing cloudinary — the library auto-parses
    # CLOUDINARY_URL at module load time and raises ValueError for any invalid format.
    # We clear it here and configure explicitly so we control the error surface.
    _os.environ.pop('CLOUDINARY_URL', None)

    import cloudinary  # noqa: PLC0415

    INSTALLED_APPS = INSTALLED_APPS + ['cloudinary_storage', 'cloudinary']  # noqa: F405
    cloudinary.config(cloudinary_url=_cloudinary_url)
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Railway terminates SSL at the load balancer and forwards HTTP internally.
# SECURE_SSL_REDIRECT must be False or Railway's health checker gets redirect-looped.
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
