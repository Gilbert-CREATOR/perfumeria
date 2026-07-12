"""
WSGI config for perfumeria project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perfumeria.settings_prod')

application = get_wsgi_application()

# Algunos servicios de Render conservan el Start Command configurado en el
# panel e ignoran Procfile/render.yaml. Sincronizar aquí garantiza que las
# credenciales secretas se apliquen al arrancar cualquier proceso WSGI.
if os.environ.get('DJANGO_SUPERUSER_USERNAME') and os.environ.get('DJANGO_SUPERUSER_PASSWORD'):
    call_command('sync_admin')
