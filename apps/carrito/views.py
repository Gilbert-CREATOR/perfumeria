from django.http import FileResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.contrib import messages
from django.urls import reverse
from .models import Carrito, ItemCarrito, Pedido, ItemPedido, MetodoEnvio, TransaccionPago
from .forms import CheckoutForm
from apps.productos.models import Producto
import paypalrestsdk
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
import json
from io import BytesIO

from .services import (
    CheckoutError,
    add_product_to_cart,
    confirmar_pago,
    crear_pedido_desde_carrito,
    liberar_reservas_vencidas,
    reintegrar_stock_pedido,
    save_pending_cart_item,
)
from .recommendations import productos_recomendados_por_temporada

@login_required
def ver_carrito(request):
    liberar_reservas_vencidas(limite=25)

    carrito, created = Carrito.objects.get_or_create(usuario=request.user)

    items = list(carrito.items.select_related('producto').all())
    total = sum(item.subtotal() for item in items)
    productos_relacionados = productos_recomendados_por_temporada(items)

    return render(request, 'carrito/carrito.html', {
        'productos': items,
        'total': total,
        'productos_relacionados': productos_relacionados,
    })



def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body or '{}')
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = {}
        requested_quantity = payload.get('cantidad', 1)
    else:
        requested_quantity = request.POST.get('cantidad', 1)

    try:
        requested_quantity = max(1, int(requested_quantity))
    except (TypeError, ValueError):
        requested_quantity = 1

    if not request.user.is_authenticated:
        if not producto.validar_stock(requested_quantity):
            error = 'No hay stock suficiente para la cantidad solicitada.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error})
            messages.error(request, error)
            return redirect('detalle_producto', producto_id=producto.id)

        save_pending_cart_item(request, producto.id, requested_quantity)
        login_url = f"{reverse('login')}?next={reverse('ver_carrito')}"
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Inicia sesión o crea una cuenta para agregar el producto.',
                'redirect': login_url,
            })
        return redirect(login_url)

    success, message = add_product_to_cart(
        request.user,
        producto.id,
        requested_quantity,
    )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': success, 'message': message, 'error': None if success else message})

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    return redirect('ver_carrito')


@login_required
def eliminar_del_carrito(request, item_id):
    carrito, created = Carrito.objects.get_or_create(usuario=request.user)
    
    try:
        item = carrito.items.get(id=item_id)
        item.delete()
        messages.success(request, 'Producto eliminado del carrito')
    except ItemCarrito.DoesNotExist:
        messages.error(request, 'El producto no está en el carrito')
    
    return redirect('ver_carrito')


@login_required
def disminuir_cantidad(request, item_id):
    carrito, created = Carrito.objects.get_or_create(usuario=request.user)
    
    try:
        item = carrito.items.get(id=item_id)
        if item.cantidad > 1:
            item.cantidad -= 1
            item.save()
            messages.success(request, 'Cantidad actualizada')
        else:
            item.delete()
            messages.success(request, 'Producto eliminado del carrito')
    except ItemCarrito.DoesNotExist:
        messages.error(request, 'El producto no está en el carrito')
    
    return redirect('ver_carrito')

@login_required
def checkout(request):
    liberar_reservas_vencidas(limite=25)
    carrito_obj, created = Carrito.objects.get_or_create(usuario=request.user)
    items = carrito_obj.items.select_related('producto').all()

    if not items.exists():
        return redirect('ver_carrito')

    # Obtener métodos de envío
    from .models import MetodoEnvio
    metodos_envio = MetodoEnvio.objects.filter(activo=True)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if not form.is_valid():
            return render(request, 'carrito/checkout_moderno.html', {
                'items': items,
                'productos': items,
                'subtotal': sum(item.subtotal() for item in items),
                'total': sum(item.subtotal() for item in items) + 5,
                'metodos_envio': metodos_envio,
                'error': 'Revisa los datos de envío y pago.',
                'form': form,
            })

        metodo_envio_obj = form.cleaned_data['metodo_envio']
        metodo_pago = form.cleaned_data['metodo_pago']

        try:
            pedido = crear_pedido_desde_carrito(
                usuario=request.user,
                metodo_envio=metodo_envio_obj,
                metodo_pago=metodo_pago,
                datos_envio={
                    campo: form.cleaned_data[campo]
                    for campo in (
                        'nombre_completo', 'telefono', 'direccion',
                        'ciudad', 'provincia', 'codigo_postal',
                    )
                },
            )
        except (CheckoutError, Carrito.DoesNotExist) as exc:
            messages.error(request, str(exc))
            return redirect('ver_carrito')

        # 🆕 Enviar email de confirmación
        try:
            from .emails import enviar_email_confirmacion_pedido
            enviar_email_confirmacion_pedido(pedido)
        except ImportError:
            print("⚠️ Módulo de emails no disponible")
        except Exception as e:
            print(f"⚠️ Error enviando email: {e}")

        messages.success(request, f'¡Pedido #{pedido.id} realizado con éxito! Total: ${pedido.total:,.1f}')

        # 🔥 REDIRECCIÓN SEGÚN MÉTODO
        if metodo_pago == 'paypal':
            return redirect('pago_paypal', pedido_id=pedido.id)

        return redirect('pedido_exitoso')

    return render(request, 'carrito/checkout_moderno.html', {
        'items': items,
        'productos': items,
        'subtotal': sum(item.subtotal() for item in items),
        'total': sum(item.subtotal() for item in items) + (metodos_envio.first().costo if metodos_envio.exists() else 0),
        'metodos_envio': metodos_envio
    })

def pedido_exitoso(request):
    # Obtener el último pedido del usuario para mostrar el número
    ultimo_pedido = None
    if request.user.is_authenticated:
        ultimo_pedido = Pedido.objects.filter(usuario=request.user).order_by('-creado').first()
    
    return render(request, 'carrito/pedido_exitoso_minimalista.html', {
        'pedido_id': ultimo_pedido.id if ultimo_pedido else None
    })

@login_required
def historial_pedidos(request):
    pedidos_usuario = Pedido.objects.filter(usuario=request.user).order_by('-creado')
    
    # Pre-cargar los items de cada pedido para optimizar
    pedidos = pedidos_usuario.prefetch_related('items__producto')

    return render(request, 'carrito/historial_moderno.html', {
        'pedidos': pedidos,
    })


@login_required
@login_required
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    items = pedido.items.all()
    
    return render(request, 'carrito/detalle_pedido.html', {
        'pedido': pedido,
        'items': items
    })


@login_required
def descargar_factura(request, pedido_id):
    pedidos = Pedido.objects.all() if request.user.is_staff else Pedido.objects.filter(usuario=request.user)
    pedido = get_object_or_404(pedidos.prefetch_related('items__producto'), pk=pedido_id)
    if pedido.estado == 'cancelado':
        messages.error(request, 'No se puede generar una factura para un pedido cancelado.')
        return redirect('detalle_pedido', pedido_id=pedido.pk)

    from .facturas import generar_factura_pdf
    buffer = BytesIO()
    generar_factura_pdf(pedido, output_path=buffer)
    buffer.seek(0)
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=f'factura_DARCY_{pedido.pk:06d}.pdf',
        content_type='application/pdf',
    )



@login_required
def pago_paypal(request, pedido_id):
    # Configurar PayPal
    from .paypal_config import configure_paypal, is_paypal_configured
    
    if not is_paypal_configured():
        messages.error(request, 'PayPal no está configurado. Contacta al administrador.')
        return redirect('detalle_pedido', pedido_id=pedido_id)
    
    if not configure_paypal():
        messages.error(request, 'Error al configurar PayPal. Intenta nuevamente.')
        return redirect('detalle_pedido', pedido_id=pedido_id)
    
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    
    # Verificación adicional de seguridad
    if pedido.usuario != request.user and not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a este pedido')
        return redirect('ver_carrito')
    
    if pedido.estado != 'pendiente':
        messages.error(request, 'Este pedido ya no puede ser pagado')
        return redirect('detalle_pedido', pedido_id=pedido.id)

    pago = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": request.build_absolute_uri(
                reverse('paypal_exito')
            ) + f"?pedido_id={pedido.id}",
            "cancel_url": request.build_absolute_uri(
                reverse('paypal_cancelado')
            ) + f"?pedido_id={pedido.id}",
        },
        "transactions": [{
            "amount": {
                "total": str(pedido.total),
                "currency": "USD"
            },
            "description": f"Pedido #{pedido.id} - Perfumería",
            "custom": str(pedido.id)  # 🆕 Importante para webhook
        }]
    })

    if pago.create():
        # Guardar la referencia para reconciliación e idempotencia.
        pedido.metodo_pago = 'paypal'
        pedido.referencia_pago = pago.id
        pedido.save(update_fields=['metodo_pago', 'referencia_pago', 'actualizado'])
        TransaccionPago.objects.update_or_create(
            referencia=pago.id,
            defaults={
                'pedido': pedido,
                'proveedor': 'paypal',
                'estado': 'pendiente',
                'monto': pedido.total,
                'moneda': 'USD',
            },
        )
        
        for link in pago.links:
            if link.rel == "approval_url":
                return redirect(link.href)
    else:
        messages.error(request, 'Error al crear el pago de PayPal')
        return redirect('detalle_pedido', pedido_id=pedido.id)


@login_required
def api_cart_count(request):
    """API endpoint para obtener el contador del carrito"""
    if not request.user.is_authenticated:
        return JsonResponse({'count': 0})
    
    try:
        carrito, created = Carrito.objects.get_or_create(usuario=request.user)
        count = carrito.items.aggregate(total=Sum('cantidad'))['total'] or 0
        return JsonResponse({'count': count})
    except Exception as e:
        return JsonResponse({'count': 0})

@login_required
def paypal_exito(request):
    """Procesa el retorno de PayPal para el dueño del pedido."""
    # Configurar PayPal
    from .paypal_config import configure_paypal, is_paypal_configured
    
    if not is_paypal_configured():
        messages.error(request, 'PayPal no está configurado. Contacta al administrador.')
        return redirect('historial_pedidos')
    
    if not configure_paypal():
        messages.error(request, 'Error al configurar PayPal. Intenta nuevamente.')
        return redirect('historial_pedidos')
    
    pedido_id = request.GET.get('pedido_id')
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    
    if not pedido_id or not payment_id or not payer_id:
        messages.error(request, 'Error en la confirmación del pago')
        return redirect('historial_pedidos')
    
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    
    # Verificación de seguridad: solo admin o dueño del pedido
    if pedido.referencia_pago and pedido.referencia_pago != payment_id:
        messages.error(request, 'La referencia de pago no corresponde a este pedido.')
        return redirect('detalle_pedido', pedido_id=pedido.id)
    
    # Ejecutar el pago
    payment = paypalrestsdk.Payment.find(payment_id)
    
    if payment.execute({"payer_id": payer_id}):
        try:
            pedido, actualizado = confirmar_pago(pedido, referencia=payment_id)
        except CheckoutError as exc:
            messages.error(request, str(exc))
            return redirect('detalle_pedido', pedido_id=pedido.id)
        TransaccionPago.objects.update_or_create(
            referencia=payment_id,
            defaults={
                'pedido': pedido, 'proveedor': 'paypal', 'estado': 'aprobada',
                'monto': pedido.total, 'moneda': 'USD',
            },
        )
        
        messages.success(request, f'¡Pago del pedido #{pedido.id} confirmado con éxito!')
        return redirect('detalle_pedido', pedido_id=pedido.id)
    else:
        messages.error(request, 'Error al procesar el pago de PayPal')
        return redirect('detalle_pedido', pedido_id=pedido.id)


@login_required
def paypal_cancelado(request):
    """Cancela una reserva de PayPal perteneciente al usuario."""
    pedido_id = request.GET.get('pedido_id')
    
    if pedido_id:
        pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
        if pedido.estado == 'pendiente':
            reintegrar_stock_pedido(pedido)
            pedido.estado = 'cancelado'
            pedido.save(update_fields=['estado', 'actualizado'])
            if pedido.referencia_pago:
                TransaccionPago.objects.filter(referencia=pedido.referencia_pago).update(estado='cancelada')
        
        messages.warning(request, f'Pago del pedido #{pedido.id} cancelado. Puedes intentarlo nuevamente.')
        return redirect('detalle_pedido', pedido_id=pedido.id)
    else:
        messages.warning(request, 'Pago cancelado')
        return redirect('historial_pedidos')




@login_required
def pago_stripe(request, pedido_id):
    get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    messages.error(request, 'El pago con tarjeta todavía no está habilitado.')
    return redirect('detalle_pedido', pedido_id=pedido_id)


@login_required
def pago_azul(request, pedido_id):
    get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    messages.error(request, 'Azul todavía no está habilitado.')
    return redirect('detalle_pedido', pedido_id=pedido_id)
