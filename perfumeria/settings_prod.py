from .settings import *
import os
from email.utils import formataddr
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
    'default': dj_database_url.parse(
        config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# 🔑 Configuración de autenticación para PostgreSQL
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# EMAIL: Resend usa HTTPS y funciona en instancias gratuitas de Render.
RESEND_API_KEY = config('RESEND_API_KEY', default='').strip()
RESEND_FROM_EMAIL = config('RESEND_FROM_EMAIL', default='').strip()
RESEND_FROM_NAME = config('RESEND_FROM_NAME', default='D.A.R.C.Y.').strip()

EMAIL_BACKEND = (
    'perfumeria.email_backends.ResendEmailBackend'
    if RESEND_API_KEY
    else 'django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com').strip()
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='').strip()
# Google muestra sus contraseñas de aplicación separadas por espacios.
EMAIL_HOST_PASSWORD = ''.join(config('EMAIL_HOST_PASSWORD', default='').split())
DEFAULT_FROM_EMAIL = formataddr((
    RESEND_FROM_NAME,
    RESEND_FROM_EMAIL if RESEND_API_KEY else EMAIL_HOST_USER,
))
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=15, cast=int)

PAYPAL_CLIENT_ID = config('PAYPAL_CLIENT_ID', default='').strip()
PAYPAL_SECRET = config('PAYPAL_SECRET', default='').strip()
PAYPAL_WEBHOOK_ID = config('PAYPAL_WEBHOOK_ID', default='').strip()
PAYPAL_MODE = config('PAYPAL_MODE', default='sandbox').strip().lower()

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
