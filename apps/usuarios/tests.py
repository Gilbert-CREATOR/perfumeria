from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase


class AutenticacionTests(TestCase):
    def test_login_acepta_email_sin_importar_mayusculas(self):
        get_user_model().objects.create_user(
            username='cliente', email='Cliente@Example.com', password='clave-segura-123'
        )
        response = self.client.post(
            '/usuarios/login/',
            {'username': 'cliente@example.com', 'password': 'clave-segura-123'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), 1)

    def test_sync_admin_actualiza_credenciales(self):
        variables = {
            'DJANGO_SUPERUSER_USERNAME': 'admin',
            'DJANGO_SUPERUSER_EMAIL': 'admin@example.com',
            'DJANGO_SUPERUSER_PASSWORD': 'una-clave-muy-segura-123',
        }
        with patch.dict('os.environ', variables):
            call_command('sync_admin')

        admin = get_user_model().objects.get(username='admin')
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password(variables['DJANGO_SUPERUSER_PASSWORD']))

    def test_rutas_de_bypass_ya_no_existen(self):
        for url in (
            '/usuarios/admin-acceso-directo/',
            '/usuarios/admin-acceso-inmediato/',
            '/usuarios/admin-panel-publico/',
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)
