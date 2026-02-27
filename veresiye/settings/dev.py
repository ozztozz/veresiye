"""
Development settings.
Usage: DJANGO_SETTINGS_MODULE=veresiye.settings.dev
       (set automatically by manage.py)
"""

from .base import *  # noqa: F401, F403

# ── Security ─────────────────────────────────────────────────────────────────
SECRET_KEY = 'django-insecure-zo*a*af9*1jqo1ykt8i5683-0h)3+nnu2cb@-w!1x-988*)7yr'

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# ── Database ──────────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── Email (print to console in dev) ──────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
