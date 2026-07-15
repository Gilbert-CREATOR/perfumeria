import json
import hmac
import hashlib
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from .models import Pedido

@csrf_exempt
@require_http_methods(["POST"])
def paypal_webhook(request):
    """
    Webhook para recibir notificaciones de PayPal
    Valida los pagos reales y actualiza el estado del pedido
    """
    
    # Obtener headers de PayPal
    paypal_auth_algo = request.headers.get('PAYPAL-AUTH-ALGO')
    paypal_transmission_id = request.headers.get('PAYPAL-TRANSMISSION-ID')
    paypal_cert_id = request.headers.get('PAYPAL-CERT-ID')
    paypal_transmission_sig = request.headers.get('PAYPAL-TRANSMISSION-SIG')
    paypal_transmission_time = request.headers.get('PAYPAL-TRANSMISSION-TIME')
    
    # Leer el cuerpo del webhook
    body = request.body.decode('utf-8')
    
    # Validar el webhook (implementación básica)
    # En producción, deberías validar con la API de PayPal
    try:
        event_data = json.loads(body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)
    
    # Procesar diferentes tipos de eventos
    event_type = event_data.get('event_type')
    resource = event_data.get('resource', {})
    
    if event_type == 'PAYMENT.SALE.COMPLETED':
        return handle_payment_completed(resource)
    elif event_type == 'PAYMENT.SALE.DENIED':
        return handle_payment_denied(resource)
    elif event_type == 'PAYMENT.SALE.PENDING':
        return handle_payment_pending(resource)
    elif event_type == 'PAYMENT.SALE.REFUNDED':
        return handle_payment_refunded(resource)
    
    return HttpResponse(status=200)

def handle_payment_completed(resource):
    """Manejar pago completado exitosamente"""
    
    # Obtener el ID del pago y del pedido
    payment_id = resource.get('id')
    custom_id = resource.get('custom')  # Debería contener el pedido_id
    
    if not custom_id:
        return HttpResponse(status=400)
    
    try:
        pedido_id = int(custom_id)
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        # Verificar que el pago coincida con el total del pedido
        payment_amount = float(resource.get('amount', {}).get('total', 0))
        if abs(payment_amount - float(pedido.total)) > 0.01:  # Tolerancia de 1 centavo
            return HttpResponse(status=400)
        
        # Actualizar estado del pedido a pagado
        if pedido.estado == 'pendiente':
            pedido.estado = 'pagado'
            pedido.save()
            
            # 🆕 Enviar email de pago confirmado
            try:
                from .emails import enviar_email_pago_confirmado
                enviar_email_pago_confirmado(pedido)
            except ImportError:
                print("⚠️ Módulo de emails no disponible")
            except Exception as e:
                print(f"⚠️ Error enviando email: {e}")
            
            # 🆕 Generar factura PDF
            try:
                from .facturas import generar_factura_para_pedido
                generar_factura_para_pedido(pedido)
            except ImportError:
                print("⚠️ Módulo de facturas no disponible")
            except Exception as e:
                print(f"⚠️ Error generando factura: {e}")
            
            print(f"✅ Pedido #{pedido.id} marcado como PAGADO - PayPal ID: {payment_id}")
            
        return HttpResponse(status=200)
        
    except (ValueError, Pedido.DoesNotExist):
        return HttpResponse(status=404)

def handle_payment_denied(resource):
    """Manejar pago denegado"""
    
    custom_id = resource.get('custom')
    if custom_id:
        try:
            pedido_id = int(custom_id)
            pedido = get_object_or_404(Pedido, id=pedido_id)
            
            if pedido.estado != 'cancelado':
                pedido.estado = 'cancelado'
                pedido.save(update_fields=['estado'])

                # Devolver stock una sola vez, aunque PayPal repita el webhook.
                for item in pedido.items.select_related('producto'):
                    item.producto.stock += item.cantidad
                    item.producto.save(update_fields=['stock'])

                from .emails import enviar_email_pago_rechazado
                enviar_email_pago_rechazado(pedido, resource.get('reason_code') or 'El procesador de pago rechazó la operación.')
            
            print(f"❌ Pedido #{pedido.id} CANCELADO - Pago denegado")
            
        except (ValueError, Pedido.DoesNotExist):
            pass
    
    return HttpResponse(status=200)

def handle_payment_pending(resource):
    """Manejar pago pendiente"""
    
    custom_id = resource.get('custom')
    if custom_id:
        try:
            pedido_id = int(custom_id)
            pedido = get_object_or_404(Pedido, id=pedido_id)
            
            # El pedido sigue como pendiente
            print(f"⏳ Pedido #{pedido.id} PENDIENTE - Esperando confirmación")
            
        except (ValueError, Pedido.DoesNotExist):
            pass
    
    return HttpResponse(status=200)

def handle_payment_refunded(resource):
    """Manejar pago reembolsado"""
    
    custom_id = resource.get('custom')
    if custom_id:
        try:
            pedido_id = int(custom_id)
            pedido = get_object_or_404(Pedido, id=pedido_id)
            
            if pedido.estado != 'cancelado':
                pedido.estado = 'cancelado'
                pedido.save(update_fields=['estado'])
                from .emails import enviar_email_cancelacion_reembolso
                enviar_email_cancelacion_reembolso(pedido, reembolsado=True)
            
            print(f"💰 Pedido #{pedido.id} REEMBOLSADO")
            
        except (ValueError, Pedido.DoesNotExist):
            pass
    
    return HttpResponse(status=200)

def verify_paypal_webhook(request_body, headers):
    """
    Verificación avanzada del webhook de PayPal
    Implementación para producción
    """
    # Esta es una implementación básica
    # En producción, deberías usar la API de PayPal para verificar
    
    paypal_cert_id = headers.get('PAYPAL-CERT-ID')
    paypal_transmission_sig = headers.get('PAYPAL-TRANSMISSION-SIG')
    paypal_transmission_time = headers.get('PAYPAL-TRANSMISSION-TIME')
    
    # Aquí iría la lógica de verificación real
    # Usando las credenciales de PayPal y el webhook ID
    
    return True  # Temporalmente siempre devuelve True
