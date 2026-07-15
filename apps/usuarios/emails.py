from django.conf import settings
from django.core import signing
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags


VERIFICACION_SALT = 'darcy-verificacion-email'


def _site_url():
    return getattr(settings, 'PUBLIC_SITE_URL', 'http://localhost:8000').rstrip('/')


def _enviar(asunto, plantilla, contexto, destinatario):
    if not destinatario:
        return False
    contexto = {
        'site_url': _site_url(),
        'catalogo_url': f'{_site_url()}{reverse("catalogo")}',
        **contexto,
    }
    html = render_to_string(plantilla, contexto)
    try:
        send_mail(
            asunto,
            strip_tags(html),
            settings.DEFAULT_FROM_EMAIL,
            [destinatario],
            html_message=html,
            fail_silently=False,
        )
    except Exception:
        return False
    return True


def crear_token_verificacion(user):
    return signing.dumps(
        {'uid': user.pk, 'email': user.email},
        salt=VERIFICACION_SALT,
        compress=True,
    )


def enviar_email_bienvenida(user):
    token = crear_token_verificacion(user)
    return _enviar(
        'Bienvenido a D.A.R.C.Y. — verifica tu correo',
        'emails/bienvenida_verificacion.html',
        {
            'usuario': user,
            'verificacion_url': f'{_site_url()}{reverse("verificar_email", args=[token])}',
        },
        user.email,
    )


def enviar_email_cuenta_eliminada(*, email, nombre, username):
    return _enviar(
        'Tu cuenta de D.A.R.C.Y. fue eliminada',
        'emails/cuenta_eliminada.html',
        {'nombre': nombre or username, 'username': username},
        email,
    )
