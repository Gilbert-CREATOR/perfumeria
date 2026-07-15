from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import reverse
from django.template.loader import render_to_string

from .emails import crear_token_verificacion, enviar_email_bienvenida, enviar_email_cuenta_eliminada
from .models import PerfilUsuario


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    PUBLIC_SITE_URL='https://darcy.example',
    DEFAULT_FROM_EMAIL='D.A.R.C.Y. <noreply@darcy.example>',
)
class CuentaYCorreosTests(TestCase):
    def test_registro_envia_bienvenida_y_verifica_el_perfil(self):
        with patch('apps.usuarios.views.enviar_email_bienvenida') as bienvenida:
            response = self.client.post(reverse('register'), {
                'username': 'nueva', 'email': 'nueva@example.com',
                'password1': 'clave-segura-123', 'password2': 'clave-segura-123',
            })
        self.assertEqual(response.status_code, 302)
        bienvenida.assert_called_once()

        user = get_user_model().objects.get(username='nueva')
        response = self.client.get(reverse('verificar_email', args=[crear_token_verificacion(user)]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PerfilUsuario.objects.get(usuario=user).email_verificado)
        self.assertTrue(enviar_email_bienvenida(user))
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('#A31523', html)
        self.assertIn(reverse('verificar_email', args=[crear_token_verificacion(user)]), html)

    def test_eliminar_cuenta_borra_credenciales_y_envia_confirmacion(self):
        user = get_user_model().objects.create_user(
            username='eliminable', email='eliminar@example.com', password='clave-segura-123'
        )
        self.client.force_login(user)
        with patch('apps.usuarios.views.enviar_email_cuenta_eliminada') as confirmacion:
            response = self.client.post(reverse('eliminar_cuenta'), {
                'username_confirmacion': 'eliminable',
                'frase_confirmacion': 'ELIMINAR MI CUENTA',
                'password': 'clave-segura-123',
            })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(get_user_model().objects.filter(username='eliminable').exists())
        self.assertFalse(self.client.login(username='eliminable', password='clave-segura-123'))
        confirmacion.assert_called_once()
        self.assertTrue(enviar_email_cuenta_eliminada(
            email='eliminar@example.com', nombre='Cliente', username='eliminable'
        ))
        self.assertIn('Cuenta eliminada', mail.outbox[0].alternatives[0][0])
        nuevo = get_user_model().objects.create_user(
            username='eliminable', email='eliminar@example.com', password='otra-clave-segura-456'
        )
        self.assertTrue(nuevo.check_password('otra-clave-segura-456'))

    def test_no_elimina_si_la_confirmacion_no_es_exacta(self):
        user = get_user_model().objects.create_user(
            username='conservar', email='conservar@example.com', password='clave-segura-123'
        )
        self.client.force_login(user)
        with patch('apps.usuarios.views.render', return_value=HttpResponse(status=200)), \
             patch('apps.usuarios.views.enviar_email_cuenta_eliminada') as confirmacion:
            response = self.client.post(reverse('eliminar_cuenta'), {
                'username_confirmacion': 'conservar',
                'frase_confirmacion': 'eliminar mi cuenta',
                'password': 'clave-segura-123',
            })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(get_user_model().objects.filter(pk=user.pk).exists())
        confirmacion.assert_not_called()

    def test_recuperacion_de_password_envia_html_disenado(self):
        html = render_to_string('emails/password_reset.html', {
            'email': 'recuperar@example.com', 'protocol': 'https',
            'domain': 'darcy.example', 'uid': 'MQ', 'token': 'token-prueba',
            'site_url': 'https://darcy.example', 'catalogo_url': 'https://darcy.example/catalogo/',
        })
        self.assertIn('RECUPERA TU', html)
        self.assertIn('#A31523', html)


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
