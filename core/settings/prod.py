"""
Production settings for Railway deployment.

Required Railway environment variables:
  DJANGO_SETTINGS_MODULE = core.settings.prod
  SECRET_KEY              = <generated>
  ALLOWED_HOSTS           = yourdomain.up.railway.app
  DATABASE_URL            = <auto-injected by Railway PostgreSQL plugin>
  REDIS_URL               = <auto-injected by Railway Redis plugin>

Media files (food images, AR models) are committed to git under media/ and
served directly by Django via the permanent /media/ route in urls.py.
No external storage service is required.

Optional S3-compatible upgrade (Backblaze B2, Cloudflare R2, AWS S3, etc.):
  S3_ENDPOINT_URL      = https://s3.us-west-004.backblazeb2.com
  S3_ACCESS_KEY_ID     = your key ID
  S3_SECRET_ACCESS_KEY = your application key / secret
  S3_BUCKET_NAME       = your bucket name
  S3_PUBLIC_DOMAIN     = optional friendly URL
"""

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
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [config('REDIS_URL')],
        },
    },
}

# ---------------------------------------------------------------------------
# S3-compatible object storage for persistent media files.
# Recommended: Backblaze B2 — free tier, no credit card required.
#   Sign up at backblaze.com → Create Bucket (Public) → App Keys → Add Key
# ---------------------------------------------------------------------------
_s3_endpoint = config('S3_ENDPOINT_URL',      default='')
_s3_key_id   = config('S3_ACCESS_KEY_ID',     default='')
_s3_secret   = config('S3_SECRET_ACCESS_KEY', default='')
_s3_bucket   = config('S3_BUCKET_NAME',       default='')
_s3_domain   = config('S3_PUBLIC_DOMAIN',     default='')  # optional friendly URL

if _s3_endpoint and _s3_key_id and _s3_secret and _s3_bucket:
    AWS_ACCESS_KEY_ID       = _s3_key_id
    AWS_SECRET_ACCESS_KEY   = _s3_secret
    AWS_STORAGE_BUCKET_NAME = _s3_bucket
    AWS_S3_ENDPOINT_URL     = _s3_endpoint
    AWS_DEFAULT_ACL         = 'public-read'   # bucket must allow public read
    AWS_QUERYSTRING_AUTH    = False            # plain public URLs, no expiry tokens
    AWS_S3_FILE_OVERWRITE   = False
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}

    if _s3_domain:
        AWS_S3_CUSTOM_DOMAIN = _s3_domain

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# ---------------------------------------------------------------------------
# Security — Railway terminates SSL at the load balancer.
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
