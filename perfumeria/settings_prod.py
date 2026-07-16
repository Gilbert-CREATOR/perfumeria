from .settings import *
import os
import dj_database_url
from decouple import config

# 🔥 PRODUCCIÓN
DEBUG = False

ALLOWED_HOSTS = [
    host.strip()
    for host in config('ALLOWED_HOSTS', default='.onrender.com').split(',')
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in config(
        'CSRF_TRUSTED_ORIGINS',
        default='https://perfumeria-darcy.onrender.com',
    ).split(',')
    if origin.strip()
]

SECRET_KEY = config('SECRET_KEY')

# 🗄️ BASE DE DATOS - POSTGRESQL CONFIGURADO CORRECTAMENTE
import dj_database_url

DATABASES = {
    'default': dj_database_url.parse(config('DATABASE_URL'))
}

# 🔑 Configuración de autenticación para PostgreSQL
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

#  EMAIL
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=15, cast=int)

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

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# 📁 MEDIA
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 🖼️ WhiteNoise para media files en producción
WHITENOISE_USE_FINDERS = True
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']

# 🧠 CACHE
CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
}

# � Configuración de Login (como en SQLite que funcionaba)
LOGIN_URL = '/usuarios/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# �📝 LOGGING (solo consola)
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
