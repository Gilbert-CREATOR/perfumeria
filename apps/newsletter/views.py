import logging
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST

from .emails import enviar_bienvenida_suscripcion
from .models import SuscriptorNewsletter


logger = logging.getLogger(__name__)


def _respuesta_json(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _redirect_estado(request, estado):
    destino = request.POST.get('next') or reverse('home')
    if not url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        destino = reverse('home')
    partes = urlsplit(destino)
    parametros = dict(parse_qsl(partes.query, keep_blank_values=True))
    parametros['newsletter'] = estado
    return redirect(urlunsplit((partes.scheme, partes.netloc, partes.path, urlencode(parametros), 'newsletter')))


@require_POST
def suscribirse(request):
    email = request.POST.get('email', '').strip().lower()
    try:
        validate_email(email)
    except ValidationError:
        mensaje = 'Escribe una dirección de correo válida.'
        if _respuesta_json(request):
            return JsonResponse({'ok': False, 'message': mensaje}, status=400)
        return _redirect_estado(request, 'invalid')

    usuario = None
    if request.user.is_authenticated and request.user.email.lower() == email:
        usuario = request.user
    elif not request.user.is_authenticated:
        usuario = User.objects.filter(email__iexact=email).order_by('id').first()

    with transaction.atomic():
        suscriptor, creado = SuscriptorNewsletter.objects.select_for_update().get_or_create(
            email=email,
            defaults={'usuario': usuario},
        )
        reactivado = not creado and not suscriptor.activo
        if not creado and (reactivado or (usuario and not suscriptor.usuario_id)):
            suscriptor.activo = True
            if usuario and not suscriptor.usuario_id:
                suscriptor.usuario = usuario
            suscriptor.save(update_fields=('activo', 'usuario', 'fecha_actualizacion'))

    if not creado and not reactivado:
        mensaje = 'Este correo ya está suscrito a D.A.R.C.Y.'
        if _respuesta_json(request):
            return JsonResponse({'ok': True, 'already_subscribed': True, 'message': mensaje})
        return _redirect_estado(request, 'already')

    try:
        enviar_bienvenida_suscripcion(suscriptor)
    except Exception:
        logger.exception('No se pudo enviar la bienvenida del newsletter a %s.', suscriptor.email)
        # Permite que la persona vuelva a intentarlo si el servidor SMTP falla.
        suscriptor.activo = False
        suscriptor.save(update_fields=('activo', 'fecha_actualizacion'))
        mensaje = 'No pudimos completar la suscripción ni enviar la bienvenida. Inténtalo más tarde.'
        if _respuesta_json(request):
            return JsonResponse({'ok': False, 'subscribed': False, 'message': mensaje}, status=503)
        return _redirect_estado(request, 'email-error')

    mensaje = '¡Gracias por suscribirte! Revisa tu correo.'
    if _respuesta_json(request):
        return JsonResponse({'ok': True, 'message': mensaje})
    return _redirect_estado(request, 'success')


@require_GET
def cancelar_confirmacion(request, token):
    suscriptor = get_object_or_404(SuscriptorNewsletter, token=token)
    return render(request, 'newsletter/cancelar.html', {'suscriptor': suscriptor})


@require_POST
def cancelar(request, token):
    suscriptor = get_object_or_404(SuscriptorNewsletter, token=token)
    if suscriptor.activo:
        suscriptor.activo = False
        suscriptor.save(update_fields=('activo', 'fecha_actualizacion'))
    return render(request, 'newsletter/cancelada.html', {'suscriptor': suscriptor})
