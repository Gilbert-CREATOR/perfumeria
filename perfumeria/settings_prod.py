"""
Configuración de Producción para Perfumería

Para usar:
export DJANGO_SETTINGS_MODULE=perfumeria.settings_prod
"""

from .settings import *
import os

# 🔥 SEGURIDAD - PRODUCCIÓN
DEBUG = False
ALLOWED_HOSTS = ['perfumeria-darcy.onrender.com', 'www.perfumeria-darcy.onrender.com', '.onrender.com']

# 🗄️ BASE DE DATOS - POSTGRESQL (Render)
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://postgres:password@localhost:5432/perfumeria_prod'
    )
}

# 🔐 SEGURIDAD
SECRET_KEY = os.environ.get('SECRET_KEY', 'cambiar-esta-clave-secreta-en-produccion')

# HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Headers de Seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# 📧 EMAIL - PRODUCCIÓN (Configurado)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'gilbertandeliz04@gmail.com'
EMAIL_HOST_PASSWORD = 'gvwa fiqu giim fyiw'
DEFAULT_FROM_EMAIL = 'noreply@perfumeria.com'

# 📁 ARCHIVOS ESTÁTICOS - PRODUCCIÓN
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 🗄️ CACHÉ - REDIS
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}

# 📝 LOGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# 🚀 PERFORMANCE
CONN_MAX_AGE = 60  # Conexiones persistentes a DB

# 📦 PAYPAL - PRODUCCIÓN (Render)
PAYPAL_MODE = 'sandbox'  # 'sandbox' para pruebas, 'live' para producción real
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', '')
PAYPAL_SECRET = os.environ.get('PAYPAL_SECRET', '')

# 🌍 VARIABLES DE ENTORNO REQUERIDAS (Render)
ENV_VARS_REQUIRED = [
    'SECRET_KEY',
    'DATABASE_URL',  # Render usa DATABASE_URL directamente
    'PAYPAL_CLIENT_ID',
    'PAYPAL_SECRET',
]

# Validar variables de entorno requeridas
for var in ENV_VARS_REQUIRED:
    if not os.environ.get(var):
        raise ValueError(f"Variable de entorno requerida: {var}")

print("🚀 Configuración de producción cargada")
