import json
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from unittest.mock import MagicMock, patch

from perfumeria.email_backends import ResendEmailBackend

from .emails import enviar_bienvenida_suscripcion
from .models import SuscriptorNewsletter
from .views import suscribirse


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='D.A.R.C.Y. <noreply@darcy.test>',
    PUBLIC_SITE_URL='https://darcy.test',
)
class NewsletterTests(TestCase):
    ajax = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

    def test_suscripcion_guarda_email_y_envia_bienvenida_disenada(self):
        with patch('apps.newsletter.views.enviar_bienvenida_suscripcion') as bienvenida:
            response = self.client.post(
                reverse('newsletter:suscribirse'),
                {'email': 'Cliente@Example.com'},
                **self.ajax,
            )

        self.assertEqual(response.status_code, 200)
        suscriptor = SuscriptorNewsletter.objects.get()
        self.assertEqual(suscriptor.email, 'cliente@example.com')
        self.assertTrue(suscriptor.activo)
        bienvenida.assert_called_once_with(suscriptor)

        self.assertTrue(enviar_bienvenida_suscripcion(suscriptor))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Gracias por suscribirte', mail.outbox[0].subject)
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('ESTÁS EN', html)
        self.assertIn('TUS FAVORITOS Y TU CARRITO', html)
        self.assertIn('SELECCIONES PARA TI', html)
        self.assertIn(str(suscriptor.token), html)
        self.assertIn('#A31523', html)

    def test_formulario_html_redirige_sin_depender_de_fetch(self):
        with patch('apps.newsletter.views.enviar_bienvenida_suscripcion'):
            response = self.client.post(
                reverse('newsletter:suscribirse'),
                {'email': 'safari@example.com', 'next': '/catalogo/?orden=nombre'},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response['Location'],
            '/catalogo/?orden=nombre&newsletter=success#newsletter',
        )

    def test_email_duplicado_no_crea_otra_suscripcion_ni_otro_correo(self):
        SuscriptorNewsletter.objects.create(email='cliente@example.com')

        response = self.client.post(
            reverse('newsletter:suscribirse'),
            {'email': 'CLIENTE@example.com'},
            **self.ajax,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['already_subscribed'])
        self.assertEqual(SuscriptorNewsletter.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_reactiva_suscripcion_y_envia_nueva_bienvenida(self):
        suscriptor = SuscriptorNewsletter.objects.create(
            email='cliente@example.com',
            activo=False,
        )

        with patch('apps.newsletter.views.enviar_bienvenida_suscripcion') as bienvenida:
            response = self.client.post(
                reverse('newsletter:suscribirse'),
                {'email': suscriptor.email},
                **self.ajax,
            )

        self.assertEqual(response.status_code, 200)
        suscriptor.refresh_from_db()
        self.assertTrue(suscriptor.activo)
        bienvenida.assert_called_once_with(suscriptor)

    def test_rechaza_email_invalido(self):
        response = self.client.post(
            reverse('newsletter:suscribirse'),
            {'email': 'correo-invalido'},
            **self.ajax,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(SuscriptorNewsletter.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_fallo_de_correo_deja_la_suscripcion_lista_para_reintentar(self):
        request = RequestFactory().post(
            reverse('newsletter:suscribirse'),
            {'email': 'cliente@example.com'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        request.user = AnonymousUser()
        with patch(
            'apps.newsletter.views.enviar_bienvenida_suscripcion',
            side_effect=RuntimeError('SMTP no disponible'),
        ):
            response = suscribirse(request)

        self.assertEqual(response.status_code, 503)
        self.assertFalse(SuscriptorNewsletter.objects.get().activo)

    def test_cancelacion_requiere_confirmacion_post(self):
        suscriptor = SuscriptorNewsletter.objects.create(email='cliente@example.com')

        html = render_to_string('newsletter/cancelar.html', {'suscriptor': suscriptor})
        self.assertIn('CONFIRMAR CANCELACIÓN', html)
        suscriptor.refresh_from_db()
        self.assertTrue(suscriptor.activo)

        with patch('apps.newsletter.views.render', return_value=HttpResponse('SUSCRIPCIÓN CANCELADA')):
            response = self.client.post(
                reverse('newsletter:cancelar_confirmar', args=[suscriptor.token])
            )
        self.assertContains(response, 'SUSCRIPCIÓN')
        suscriptor.refresh_from_db()
        self.assertFalse(suscriptor.activo)

    @override_settings(
        RESEND_API_KEY='re_api-key-prueba',
        RESEND_FROM_EMAIL='notificaciones@darcy.example',
        RESEND_FROM_NAME='D.A.R.C.Y.',
    )
    def test_backend_resend_envia_html_por_https(self):
        message = EmailMultiAlternatives(
            subject='Correo de prueba',
            body='Versión de texto',
            from_email='D.A.R.C.Y. <notificaciones@darcy.example>',
            to=['Cliente <cliente@example.com>'],
            reply_to=['soporte@darcy.example'],
        )
        message.attach_alternative('<strong>Correo diseñado</strong>', 'text/html')
        response = MagicMock(status=200)
        response.__enter__.return_value = response

        with patch('perfumeria.email_backends.urlopen', return_value=response) as urlopen_mock:
            sent = ResendEmailBackend().send_messages([message])

        self.assertEqual(sent, 1)
        request = urlopen_mock.call_args.args[0]
        payload = json.loads(request.data.decode('utf-8'))
        self.assertEqual(request.full_url, 'https://api.resend.com/emails')
        self.assertEqual(request.headers['Authorization'], 'Bearer re_api-key-prueba')
        self.assertEqual(payload['from'], 'D.A.R.C.Y. <notificaciones@darcy.example>')
        self.assertEqual(payload['to'][0], 'Cliente <cliente@example.com>')
        self.assertEqual(payload['html'], '<strong>Correo diseñado</strong>')
        self.assertEqual(payload['reply_to'], 'soporte@darcy.example')
