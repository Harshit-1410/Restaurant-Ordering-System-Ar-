"""
Production settings for Railway deployment.

Required Railway environment variables:
  DJANGO_SETTINGS_MODULE = core.settings.prod
  SECRET_KEY              = <generated>
  ALLOWED_HOSTS           = yourdomain.up.railway.app
  DATABASE_URL            = <auto-injected by Railway PostgreSQL plugin>
  REDIS_URL               = <auto-injected by Railway Redis plugin>

Cloudflare R2 media storage (optional — falls back to ephemeral local storage):
  R2_ACCOUNT_ID       = your Cloudflare account ID
  R2_ACCESS_KEY_ID    = R2 API token access key
  R2_SECRET_ACCESS_KEY = R2 API token secret key
  R2_BUCKET_NAME      = your bucket name  (e.g. ar-restaurant-media)
  R2_PUBLIC_DOMAIN    = pub-xxxx.r2.dev  (from bucket → Public Access tab)
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
# Cloudflare R2 — persistent CDN-backed media storage.
# Free tier: 10 GB storage, 1 M writes/month, no egress fees, no file-size cap.
# All four R2_* variables must be set; if any are missing the app falls back
# to Railway's ephemeral local filesystem (files lost on redeploy).
# ---------------------------------------------------------------------------
_r2_account_id    = config('R2_ACCOUNT_ID',        default='')
_r2_access_key    = config('R2_ACCESS_KEY_ID',      default='')
_r2_secret_key    = config('R2_SECRET_ACCESS_KEY',  default='')
_r2_bucket        = config('R2_BUCKET_NAME',        default='')
_r2_public_domain = config('R2_PUBLIC_DOMAIN',      default='')  # pub-xxx.r2.dev

if _r2_account_id and _r2_access_key and _r2_secret_key and _r2_bucket:
    AWS_ACCESS_KEY_ID       = _r2_access_key
    AWS_SECRET_ACCESS_KEY   = _r2_secret_key
    AWS_STORAGE_BUCKET_NAME = _r2_bucket
    AWS_S3_ENDPOINT_URL     = f'https://{_r2_account_id}.r2.cloudflarestorage.com'
    AWS_QUERYSTRING_AUTH    = False   # serve public URLs, no expiring signed tokens
    AWS_DEFAULT_ACL         = None    # R2 uses bucket-level public access, not per-object ACLs
    AWS_S3_FILE_OVERWRITE   = False   # keep old file if same name is re-uploaded
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}  # 1-day browser cache

    if _r2_public_domain:
        # Files will be served as https://<r2_public_domain>/<key>
        AWS_S3_CUSTOM_DOMAIN = _r2_public_domain

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
