from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags


def _site_url():
    return getattr(settings, 'PUBLIC_SITE_URL', 'http://localhost:8000').rstrip('/')


def enviar_bienvenida_suscripcion(suscriptor):
    site_url = _site_url()
    contexto = {
        'site_url': site_url,
        'catalogo_url': f'{site_url}{reverse("catalogo")}',
        'email': suscriptor.email,
        'cancelar_url': (
            f'{site_url}'
            f'{reverse("newsletter:cancelar", args=[suscriptor.token])}'
        ),
    }
    html = render_to_string('emails/newsletter_bienvenida.html', contexto)
    send_mail(
        'Gracias por suscribirte a D.A.R.C.Y.',
        strip_tags(html),
        settings.DEFAULT_FROM_EMAIL,
        [suscriptor.email],
        html_message=html,
        fail_silently=False,
    )
    return True
