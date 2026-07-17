import base64
import json
import logging
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Pedido, TransaccionPago
from .services import CheckoutError, confirmar_pago, reintegrar_stock_pedido


logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def paypal_webhook(request):
    """Valida con PayPal y procesa el evento de forma idempotente."""
    try:
        event_data = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return HttpResponse(status=400)

    if not verify_paypal_webhook(event_data, request.headers):
        return HttpResponse(status=401)

    event_type = event_data.get('event_type')
    resource = event_data.get('resource') or {}
    if event_type in {'PAYMENT.SALE.COMPLETED', 'PAYMENT.CAPTURE.COMPLETED'}:
        return handle_payment_completed(resource)
    if event_type in {'PAYMENT.SALE.DENIED', 'PAYMENT.CAPTURE.DENIED'}:
        return handle_payment_denied(resource)
    if event_type in {'PAYMENT.SALE.PENDING', 'PAYMENT.CAPTURE.PENDING'}:
        return handle_payment_pending(resource)
    if event_type in {'PAYMENT.SALE.REFUNDED', 'PAYMENT.CAPTURE.REFUNDED'}:
        return handle_payment_refunded(resource)
    return HttpResponse(status=200)


def _pedido_desde_recurso(resource):
    custom_id = resource.get('custom') or resource.get('custom_id')
    try:
        pedido_id = int(custom_id)
    except (TypeError, ValueError):
        return None
    return Pedido.objects.filter(pk=pedido_id).first()


def _importe_recurso(resource):
    amount = resource.get('amount') or {}
    raw = amount.get('total', amount.get('value', '0'))
    try:
        return Decimal(str(raw)), amount.get('currency') or amount.get('currency_code') or 'USD'
    except (InvalidOperation, TypeError):
        return None, None


def _guardar_transaccion(*, pedido, resource, estado):
    referencia = resource.get('id')
    if not referencia:
        return
    monto, moneda = _importe_recurso(resource)
    TransaccionPago.objects.update_or_create(
        referencia=referencia,
        defaults={
            'pedido': pedido,
            'proveedor': 'paypal',
            'estado': estado,
            'monto': monto if monto is not None else pedido.total,
            'moneda': (moneda or 'USD')[:3],
            'respuesta': resource,
        },
    )


def handle_payment_completed(resource):
    pedido = _pedido_desde_recurso(resource)
    if not pedido:
        return HttpResponse(status=404)

    payment_amount, currency = _importe_recurso(resource)
    if payment_amount is None or payment_amount != pedido.total or currency != 'USD':
        logger.warning('Importe PayPal no coincide para pedido %s', pedido.pk)
        return HttpResponse(status=400)

    try:
        pedido, changed = confirmar_pago(pedido, referencia=resource.get('id', ''))
    except CheckoutError:
        return HttpResponse(status=409)
    _guardar_transaccion(pedido=pedido, resource=resource, estado='aprobada')

    if changed:
        try:
            from .emails import enviar_email_pago_confirmado
            enviar_email_pago_confirmado(pedido)
        except Exception:
            logger.exception('No se pudo enviar el correo de pago del pedido %s', pedido.pk)
        try:
            from .facturas import generar_factura_para_pedido
            generar_factura_para_pedido(pedido)
        except Exception:
            logger.exception('No se pudo generar la factura del pedido %s', pedido.pk)
    return HttpResponse(status=200)


def handle_payment_denied(resource):
    pedido = _pedido_desde_recurso(resource)
    if not pedido:
        return HttpResponse(status=200)
    _guardar_transaccion(pedido=pedido, resource=resource, estado='rechazada')
    if pedido.estado == 'pendiente':
        reintegrar_stock_pedido(pedido)
        Pedido.objects.filter(pk=pedido.pk, estado='pendiente').update(estado='cancelado')
        try:
            from .emails import enviar_email_pago_rechazado
            enviar_email_pago_rechazado(
                pedido,
                resource.get('reason_code') or 'El procesador de pago rechazó la operación.',
            )
        except Exception:
            logger.exception('No se pudo enviar el correo de pago rechazado %s', pedido.pk)
    return HttpResponse(status=200)


def handle_payment_pending(resource):
    pedido = _pedido_desde_recurso(resource)
    if pedido:
        _guardar_transaccion(pedido=pedido, resource=resource, estado='pendiente')
    return HttpResponse(status=200)


def handle_payment_refunded(resource):
    pedido = _pedido_desde_recurso(resource)
    if not pedido:
        return HttpResponse(status=200)
    _guardar_transaccion(pedido=pedido, resource=resource, estado='reembolsada')
    if pedido.estado != 'cancelado':
        reintegrar_stock_pedido(pedido)
        Pedido.objects.filter(pk=pedido.pk).update(estado='cancelado')
        try:
            from .emails import enviar_email_cancelacion_reembolso
            enviar_email_cancelacion_reembolso(pedido, reembolsado=True)
        except Exception:
            logger.exception('No se pudo enviar el correo de reembolso %s', pedido.pk)
    return HttpResponse(status=200)


def _paypal_api_base():
    if getattr(settings, 'PAYPAL_MODE', 'sandbox') == 'live':
        return 'https://api-m.paypal.com'
    return 'https://api-m.sandbox.paypal.com'


def _paypal_access_token():
    client_id = getattr(settings, 'PAYPAL_CLIENT_ID', '')
    secret = getattr(settings, 'PAYPAL_SECRET', '')
    if not client_id or not secret:
        return None
    credentials = base64.b64encode(f'{client_id}:{secret}'.encode()).decode()
    request = Request(
        f'{_paypal_api_base()}/v1/oauth2/token',
        data=b'grant_type=client_credentials',
        headers={
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method='POST',
    )
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode()).get('access_token')


def verify_paypal_webhook(event_body, headers):
    """Verifica la firma consultando el endpoint oficial de PayPal."""
    webhook_id = getattr(settings, 'PAYPAL_WEBHOOK_ID', '')
    required = {
        'auth_algo': headers.get('PAYPAL-AUTH-ALGO'),
        'cert_url': headers.get('PAYPAL-CERT-URL'),
        'transmission_id': headers.get('PAYPAL-TRANSMISSION-ID'),
        'transmission_sig': headers.get('PAYPAL-TRANSMISSION-SIG'),
        'transmission_time': headers.get('PAYPAL-TRANSMISSION-TIME'),
    }
    if not webhook_id or not all(required.values()):
        return False
    try:
        token = _paypal_access_token()
        if not token:
            return False
        payload = {**required, 'webhook_id': webhook_id, 'webhook_event': event_body}
        request = Request(
            f'{_paypal_api_base()}/v1/notifications/verify-webhook-signature',
            data=json.dumps(payload).encode(),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        with urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode())
        return result.get('verification_status') == 'SUCCESS'
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        logger.exception('No fue posible verificar la firma del webhook de PayPal')
        return False
