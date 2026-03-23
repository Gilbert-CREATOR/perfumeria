"""
Configuración de Producción para Perfumería D.A.R.C.Y.

Para usar:
export DJANGO_SETTINGS_MODULE=perfumeria.settings_prod
"""

from .settings import *
import os
import dj_database_url

# 🔥 SEGURIDAD - PRODUCCIÓN
DEBUG = False

# Hosts permitidos
ALLOWED_HOSTS = [".onrender.com"]

# 🔐 SECRET KEY (desde Render)
SECRET_KEY = os.environ.get('SECRET_KEY')

# 🗄️ BASE DE DATOS - PostgreSQL desde Render
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        engine='django.db.backends.postgresql'
    )
}

# 🔐 SEGURIDAD HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Headers de Seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# 📧 EMAIL (desde variables de entorno)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'gilbertandeliz04@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'gvwa fiqu giim fyiw')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@perfumeria.com')

# 📁 ARCHIVOS ESTÁTICOS
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoise (servir estáticos)
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 📁 MEDIA FILES
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 🧠 CACHE (SIN REDIS)
CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
}

# 📝 LOGGING (solo consola para evitar errores)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}

# 🚀 PERFORMANCE
CONN_MAX_AGE = 60

# 💳 PAYPAL (desde variables de entorno)
PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
PAYPAL_SECRET = os.environ.get('PAYPAL_SECRET')

# 🌍 VALIDACIÓN DE VARIABLES IMPORTANTES
REQUIRED_ENV_VARS = [
    'SECRET_KEY',
    'DATABASE_URL',
    'EMAIL_HOST',
    'EMAIL_PORT',
    'EMAIL_HOST_USER',
    'EMAIL_HOST_PASSWORD',
    'DEFAULT_FROM_EMAIL'
]

for var in REQUIRED_ENV_VARS:
    if not os.environ.get(var):
        raise ValueError(f"Falta la variable de entorno: {var}")

print("🚀 Configuración de producción cargada correctamente")