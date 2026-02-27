"""
Production settings.
Usage: DJANGO_SETTINGS_MODULE=veresiye.settings.prod
       (set automatically by wsgi.py / asgi.py)

Required environment variables:
  SECRET_KEY  – a long random string, never commit this value
"""

import os
from .base import *  # noqa: F401, F403

# ── Security ─────────────────────────────────────────────────────────────────
SECRET_KEY = 'django-insecure-zo*a*af9*1jqo1ykt8i5683-0h)3+nnu2cb@-w!1x-988*)7yr'

DEBUG = False

ALLOWED_HOSTS = [
    'ozz1.pythonanywhere.com',
    'bizimbakkal.pythonanywhere.com',
]

# ── Database ──────────────────────────────────────────────────────────────────

DATABASE_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'database'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATABASE_DIR / 'veresiye.sqlite3',
    }
}

# ── HTTPS / Cookie security ───────────────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000        # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ── Email ─────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
