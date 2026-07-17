import sys
from unittest import skipIf

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.newsletter.models import SuscriptorNewsletter
from .models import MensajeContacto, PreguntaFrecuente


class PanelOperativoTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='gestor', email='gestor@example.com', password='UnaClaveSegura1', is_staff=True
        )

    def test_paneles_nuevos_exigen_administrador(self):
        for nombre in ('admin_usuarios', 'admin_newsletter', 'admin_configuracion', 'admin_faq', 'admin_mensajes'):
            respuesta = self.client.get(reverse(nombre))
            self.assertEqual(respuesta.status_code, 302)

    @skipIf(sys.version_info >= (3, 14), 'Django 4.2 no instrumenta plantillas correctamente en Python 3.14')
    def test_administrador_accede_a_los_paneles(self):
        self.client.force_login(self.admin)
        for nombre in ('admin_usuarios', 'admin_newsletter', 'admin_configuracion', 'admin_faq', 'admin_mensajes'):
            respuesta = self.client.get(reverse(nombre))
            self.assertEqual(respuesta.status_code, 200, nombre)

    def test_administrador_no_puede_desactivarse(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('admin_usuario_toggle', args=[self.admin.pk]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_controla_faq_y_newsletter(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('admin_faq_crear'), {
            'pregunta': '¿Hacen envíos?', 'respuesta': 'Sí.', 'orden': 1, 'activa': 'on',
        })
        self.assertTrue(PreguntaFrecuente.objects.filter(pregunta='¿Hacen envíos?').exists())
        suscriptor = SuscriptorNewsletter.objects.create(email='cliente@example.com')
        self.client.post(reverse('admin_newsletter_toggle', args=[suscriptor.pk]))
        suscriptor.refresh_from_db()
        self.assertFalse(suscriptor.activo)


class ContactoPublicoTests(TestCase):
    def test_formulario_guarda_mensaje_para_el_panel(self):
        respuesta = self.client.post(reverse('contacto'), {
            'nombre': 'Cliente', 'email': 'cliente@example.com', 'telefono': '123',
            'asunto': 'producto', 'mensaje': 'Necesito información.', 'urgente': 'on',
        })
        self.assertRedirects(respuesta, reverse('contacto'), fetch_redirect_response=False)
        mensaje = MensajeContacto.objects.get()
        self.assertEqual(mensaje.estado, 'nuevo')
        self.assertTrue(mensaje.urgente)
