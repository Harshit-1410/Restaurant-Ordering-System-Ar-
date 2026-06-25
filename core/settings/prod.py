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

import cloudinary
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
INSTALLED_APPS = INSTALLED_APPS + ['cloudinary_storage', 'cloudinary']  # noqa: F405

cloudinary.config(cloudinary_url=config('CLOUDINARY_URL'))

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
