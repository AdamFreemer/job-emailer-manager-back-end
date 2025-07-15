"""
Local development settings
"""
from .base import *

DEBUG = True

# For development, we'll use SQLite initially to make it easier
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Development-specific settings
CORS_ALLOW_ALL_ORIGINS = True

# Celery - for development, run synchronously
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'