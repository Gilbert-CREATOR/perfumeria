from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags

def enviar_email_confirmacion_pedido(pedido):
    """
    Envía email de confirmación cuando se crea un pedido
    """
    
    subject = f"🛒 Tu Pedido #{pedido.id} ha sido recibido"
    
    context = {
        'pedido': pedido,
        'items': pedido.items.select_related('producto').all(),
        'direccion_completa': f"{pedido.direccion}, {pedido.ciudad}, {pedido.provincia}, {pedido.codigo_postal}",
        'nombre_cliente': pedido.nombre_completo or pedido.usuario.username,
    }
    
    html_message = render_to_string('emails/confirmacion_pedido.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pedido.usuario.email],
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
    
    subject = f"💰 ¡Pago Confirmado! Tu Pedido #{pedido.id}"
    
    context = {
        'pedido': pedido,
        'items': pedido.items.select_related('producto').all(),
        'nombre_cliente': pedido.nombre_completo or pedido.usuario.username,
    }
    
    html_message = render_to_string('emails/pago_confirmado.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pedido.usuario.email],
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
    
    if not pedido.envio:
        return False
    
    subject = f"📦 Tu Pedido #{pedido.id} ha sido despachado"
    
    context = {
        'pedido': pedido,
        'envio': pedido.envio,
        'nombre_cliente': pedido.nombre_completo or pedido.usuario.username,
        'numero_seguimiento': pedido.envio.numero_seguimiento or 'Pendiente',
    }
    
    html_message = render_to_string('emails/envio_despachado.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pedido.usuario.email],
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
    
    subject = f"✅ ¡Pedido Entregado! Tu Pedido #{pedido.id}"
    
    context = {
        'pedido': pedido,
        'items': pedido.items.select_related('producto').all(),
        'nombre_cliente': pedido.nombre_completo or pedido.usuario.username,
    }
    
    html_message = render_to_string('emails/pedido_entregado.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pedido.usuario.email],
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
    
    subject = "🛒 ¿Olvidaste algo en tu carrito?"
    
    total = sum(item.subtotal() for item in items)
    
    context = {
        'usuario': usuario,
        'items': items,
        'total': total,
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
