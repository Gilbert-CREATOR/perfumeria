"""
Configuración de Producción para Perfumería

Para usar:
export DJANGO_SETTINGS_MODULE=perfumeria.settings_prod
"""

from .settings import *
import os

# 🔥 SEGURIDAD - PRODUCCIÓN
DEBUG = False
ALLOWED_HOSTS = ['perfumeria-tu-dominio.com', 'www.perfumeria-tu-dominio.com', 'localhost']

# 🗄️ BASE DE DATOS - POSTGRESQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'perfumeria_prod'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
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

# 📧 EMAIL - PRODUCCIÓN
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@perfumeria.com')

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

# 📦 PAYPAL - PRODUCCIÓN
PAYPAL_MODE = 'live'  # Cambiar a 'live' en producción real
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', '')
PAYPAL_SECRET = os.environ.get('PAYPAL_SECRET', '')

# 🌍 VARIABLES DE ENTORNO REQUERIDAS
ENV_VARS_REQUIRED = [
    'SECRET_KEY',
    'DB_NAME',
    'DB_USER', 
    'DB_PASSWORD',
    'PAYPAL_CLIENT_ID',
    'PAYPAL_SECRET',
]

# Validar variables de entorno requeridas
for var in ENV_VARS_REQUIRED:
    if not os.environ.get(var):
        raise ValueError(f"Variable de entorno requerida: {var}")

print("🚀 Configuración de producción cargada")
