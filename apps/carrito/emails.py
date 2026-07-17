from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags
from decimal import Decimal

from .recommendations import productos_recomendados_por_temporada


def _site_url():
    return getattr(
        settings,
        'PUBLIC_SITE_URL',
        'https://perfumeria-darcy.onrender.com',
    ).rstrip('/')


def _absolute_url(path):
    return f'{_site_url()}{path}'


def _pedido_context(pedido):
    items = list(pedido.items.select_related('producto').all())
    usuario = pedido.usuario
    return {
        'pedido': pedido,
        'items': items,
        'nombre_cliente': (
            pedido.nombre_completo
            or (usuario.get_full_name() if usuario else '')
            or (usuario.username if usuario else 'Cliente')
        ),
        'site_url': _site_url(),
        'pedido_url': _absolute_url(reverse('detalle_pedido', args=[pedido.id])),
        'catalogo_url': _absolute_url(reverse('catalogo')),
    }


def _enviar_correo_html(subject, template, context, destinatario):
    if not destinatario:
        return False
    html_message = render_to_string(template, context)
    try:
        send_mail(
            subject=subject,
            message=strip_tags(html_message),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as error:
        print(f'Error enviando {template}: {error}')
        return False


def _email_pedido(pedido):
    return pedido.usuario.email if pedido.usuario else ''

def enviar_email_confirmacion_pedido(pedido):
    """
    Envía email de confirmación cuando se crea un pedido
    """
    
    subject = f"D.A.R.C.Y. — Recibimos tu pedido #{pedido.id}"
    
    context = {
        **_pedido_context(pedido),
        'direccion_completa': f"{pedido.direccion}, {pedido.ciudad}, {pedido.provincia}, {pedido.codigo_postal}",
    }
    
    html_message = render_to_string('emails/confirmacion_pedido.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[_email_pedido(pedido)],
            html_message=html_message,
            fail_silently=False
        )
        print(f"✅ Email de confirmación enviado para pedido #{pedido.id}")
        return True
    except Exception as e:
        print(f"❌ Error enviando email de confirmación: {e}")
        return False

def enviar_email_pago_confirmado(pedido):
    """
    Envía email cuando el pago es confirmado
    """
    
    subject = f"D.A.R.C.Y. — Pago confirmado para tu pedido #{pedido.id}"
    
    context = _pedido_context(pedido)
    
    html_message = render_to_string('emails/pago_confirmado.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[_email_pedido(pedido)],
            html_message=html_message,
            fail_silently=False
        )
        print(f"✅ Email de pago confirmado enviado para pedido #{pedido.id}")
        return True
    except Exception as e:
        print(f"❌ Error enviando email de pago confirmado: {e}")
        return False

def enviar_email_envio_despachado(pedido):
    """
    Envía email cuando el pedido es despachado
    """
    
    if not hasattr(pedido, 'envio'):
        return False
    
    subject = f"D.A.R.C.Y. — Tu pedido #{pedido.id} está en camino"
    
    context = {
        **_pedido_context(pedido),
        'envio': pedido.envio,
        'numero_seguimiento': pedido.envio.numero_seguimiento or 'Pendiente',
    }
    
    html_message = render_to_string('emails/envio_despachado.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[_email_pedido(pedido)],
            html_message=html_message,
            fail_silently=False
        )
        print(f"✅ Email de envío despachado enviado para pedido #{pedido.id}")
        return True
    except Exception as e:
        print(f"❌ Error enviando email de envío despachado: {e}")
        return False

def enviar_email_pedido_entregado(pedido):
    """
    Envía email cuando el pedido es entregado
    """
    
    subject = f"D.A.R.C.Y. — Tu pedido #{pedido.id} fue entregado"
    
    context = _pedido_context(pedido)
    
    html_message = render_to_string('emails/pedido_entregado.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[_email_pedido(pedido)],
            html_message=html_message,
            fail_silently=False
        )
        print(f"✅ Email de pedido entregado enviado para pedido #{pedido.id}")
        return True
    except Exception as e:
        print(f"❌ Error enviando email de pedido entregado: {e}")
        return False

def enviar_email_carrito_abandonado(usuario, items):
    """
    Envía email de recordatorio de carrito abandonado
    """
    
    subject = "D.A.R.C.Y. — Tu selección sigue esperándote"
    
    items = list(items)
    total = sum(
        (Decimal(str(item.producto.precio)) * item.cantidad for item in items),
        Decimal('0'),
    )
    
    context = {
        'usuario': usuario,
        'items': items,
        'total': total,
        'nombre_cliente': usuario.get_full_name() or usuario.username,
        'site_url': _site_url(),
        'carrito_url': _absolute_url(reverse('ver_carrito')),
        'catalogo_url': _absolute_url(reverse('catalogo')),
    }
    
    html_message = render_to_string('emails/carrito_abandonado.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            html_message=html_message,
            fail_silently=False
        )
        print(f"✅ Email de carrito abandonado enviado para {usuario.username}")
        return True
    except Exception as e:
        print(f"❌ Error enviando email de carrito abandonado: {e}")
        return False


def enviar_email_pago_rechazado(pedido, motivo='El procesador de pago rechazó la operación.'):
    context = {
        **_pedido_context(pedido),
        'motivo': motivo,
        'checkout_url': _absolute_url(reverse('catalogo')),
    }
    return _enviar_correo_html(
        f'D.A.R.C.Y. — No pudimos procesar el pago del pedido #{pedido.id}',
        'emails/pago_rechazado.html',
        context,
        _email_pedido(pedido),
    )


def enviar_email_pedido_preparacion(pedido):
    context = _pedido_context(pedido)
    return _enviar_correo_html(
        f'D.A.R.C.Y. — Estamos preparando tu pedido #{pedido.id}',
        'emails/pedido_preparacion.html',
        context,
        _email_pedido(pedido),
    )


def enviar_email_cancelacion_reembolso(pedido, reembolsado=False):
    context = {
        **_pedido_context(pedido),
        'reembolsado': reembolsado,
    }
    asunto_estado = 'Reembolso procesado' if reembolsado else 'Pedido cancelado'
    return _enviar_correo_html(
        f'D.A.R.C.Y. — {asunto_estado} para el pedido #{pedido.id}',
        'emails/cancelacion_reembolso.html',
        context,
        _email_pedido(pedido),
    )


def enviar_email_producto_disponible(usuario, producto):
    context = {
        'usuario': usuario,
        'nombre_cliente': usuario.get_full_name() or usuario.username,
        'producto': producto,
        'site_url': _site_url(),
        'producto_url': _absolute_url(reverse('detalle_producto', args=[producto.id])),
        'catalogo_url': _absolute_url(reverse('catalogo')),
    }
    return _enviar_correo_html(
        f'D.A.R.C.Y. — {producto.nombre} volvió a estar disponible',
        'emails/producto_disponible.html',
        context,
        usuario.email,
    )


def enviar_email_recomendaciones(pedido):
    items = list(pedido.items.select_related('producto').all())
    productos = productos_recomendados_por_temporada(items, limite=4)
    if not productos:
        return False
    context = {
        **_pedido_context(pedido),
        'productos_recomendados': productos,
    }
    return _enviar_correo_html(
        'D.A.R.C.Y. — Seleccionamos estas fragancias para ti',
        'emails/recomendaciones.html',
        context,
        _email_pedido(pedido),
    )


def enviar_email_solicitud_resena(pedido):
    context = _pedido_context(pedido)
    return _enviar_correo_html(
        f'D.A.R.C.Y. — ¿Qué te pareció tu pedido #{pedido.id}?',
        'emails/solicitud_resena.html',
        context,
        _email_pedido(pedido),
    )
