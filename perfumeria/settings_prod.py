from .settings import *
import os
import dj_database_url
from decouple import config

# 🔥 PRODUCCIÓN
DEBUG = False

ALLOWED_HOSTS = [".onrender.com"]

SECRET_KEY = config('SECRET_KEY')

# 🗄️ BASE DE DATOS - POSTGRESQL (Render)
import dj_database_url

# Usar PostgreSQL de Render con DATABASE_URL
DATABASES = {
    'default': dj_database_url.parse(config('DATABASE_URL'))
}

#  EMAIL
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

# STATIC FILES
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

# WhiteNoise
MIDDLEWARE = MIDDLEWARE.copy()
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 📁 MEDIA
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 🧠 CACHE
CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
}

# 📝 LOGGING (solo consola)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

print("🚀 Configuración de producción cargada correctamente")