from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.contrib import messages
from django.urls import reverse
from .models import Carrito, ItemCarrito, Pedido, ItemPedido, MetodoEnvio
from apps.productos.models import Producto
import paypalrestsdk
from django.conf import settings

paypalrestsdk.configure({
    "mode": "sandbox",  # cambiar a "live" en producción
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_SECRET,
})


@login_required
def ver_carrito(request):
    if not request.user.is_authenticated:
        return redirect('/admin/login/')  # temporal

    carrito, created = Carrito.objects.get_or_create(usuario=request.user)

    items = carrito.items.select_related('producto').all()
    total = sum(item.subtotal() for item in items)

    return render(request, 'carrito/carrito.html', {
        'productos': items,
        'total': total
    })



@login_required
def agregar_al_carrito(request, producto_id):
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Debes iniciar sesión'})
        return redirect('ver_carrito')

    producto = get_object_or_404(Producto, id=producto_id)
    
    # Validar stock
    if not producto.validar_stock():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'No hay stock disponible'})
        messages.error(request, 'No hay stock disponible')
        return redirect('ver_carrito')

    carrito, created = Carrito.objects.get_or_create(usuario=request.user)

    item, created = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        producto=producto
    )

    if not created:
        # Validar stock si se aumenta la cantidad
        if not producto.validar_stock(item.cantidad + 1):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': f'Stock insuficiente. Solo quedan {producto.stock} unidades'})
            messages.error(request, f'Stock insuficiente. Solo quedan {producto.stock} unidades')
        else:
            item.cantidad += 1
            item.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': f'Se agregó otra unidad de {producto.nombre}'})
            messages.success(request, f'Se agregó otra unidad de {producto.nombre} al carrito')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'{producto.nombre} agregado al carrito'})
        messages.success(request, f'{producto.nombre} agregado al carrito')

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
    carrito_obj, created = Carrito.objects.get_or_create(usuario=request.user)
    items = carrito_obj.items.select_related('producto').all()

    if not items.exists():
        return redirect('ver_carrito')

    # Obtener métodos de envío
    from .models import MetodoEnvio
    metodos_envio = MetodoEnvio.objects.filter(activo=True)

    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago')
        metodo_envio = request.POST.get('metodo_envio')  # Cambiado de metodo_envio_id

        # Obtener datos de dirección
        nombre_completo = request.POST.get('nombre_completo')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        ciudad = request.POST.get('ciudad')
        provincia = request.POST.get('provincia')
        codigo_postal = request.POST.get('codigo_postal')

        # Validar campos requeridos
        if not all([nombre_completo, telefono, direccion, ciudad, provincia, codigo_postal, metodo_envio]):
            return render(request, 'carrito/checkout_moderno.html', {
                'items': items,
                'productos': items,
                'subtotal': sum(item.subtotal() for item in items),
                'total': sum(item.subtotal() for item in items) + 5,
                'metodos_envio': metodos_envio,
                'error': 'Todos los campos son obligatorios'
            })

        # Obtener método de envío (ahora usamos el valor directo)
        costo_envio = 0
        metodo_envio_obj = None
        
        if metodo_envio == 'estandar':
            costo_envio = 5
            metodo_envio_obj, _ = MetodoEnvio.objects.get_or_create(
                nombre='Envío Estándar',
                defaults={
                    'costo': 5,
                    'tiempo_entrega': '3-5 días',
                    'activo': True
                }
            )
        elif metodo_envio == 'express':
            costo_envio = 15
            metodo_envio_obj, _ = MetodoEnvio.objects.get_or_create(
                nombre='Envío Express',
                defaults={
                    'costo': 15,
                    'tiempo_entrega': '1-2 días',
                    'activo': True
                }
            )
        elif metodo_envio == 'tienda':
            costo_envio = 0
            metodo_envio_obj, _ = MetodoEnvio.objects.get_or_create(
                nombre='Recoger en Tienda',
                defaults={
                    'costo': 0,
                    'tiempo_entrega': 'Mismo día',
                    'activo': True
                }
            )

        # Validar stock de todos los productos
        for item in items:
            if not item.producto.validar_stock(item.cantidad):
                return render(request, 'carrito/checkout_moderno.html', {
                    'items': items,
                    'productos': items,
                    'subtotal': sum(item.subtotal() for item in items),
                    'total': sum(item.subtotal() for item in items) + 5,
                    'metodos_envio': metodos_envio,
                    'error': f'Stock insuficiente para {item.producto.nombre}. Solo quedan {item.producto.stock} unidades.'
                })

        subtotal = sum(item.subtotal() for item in items)
        total = subtotal + costo_envio

        pedido = Pedido.objects.create(
            usuario=request.user,
            metodo_pago=metodo_pago,
            subtotal=subtotal,
            costo_envio=costo_envio,
            total=total,
            nombre_completo=nombre_completo,
            telefono=telefono,
            direccion=direccion,
            ciudad=ciudad,
            provincia=provincia,
            codigo_postal=codigo_postal
        )

        # Crear items del pedido
        for item in items:
            ItemPedido.objects.create(
                pedido=pedido,
                producto=item.producto,
                cantidad=item.cantidad,
                precio=item.producto.precio
            )

            # Descontar stock
            item.producto.descontar_stock(item.cantidad)

        # Crear envío
        from .models import Envio
        envio = Envio.objects.create(
            pedido=pedido,
            metodo_envio=metodo_envio_obj  # Usamos el objeto MetodoEnvio
        )

        # limpiar carrito
        items.delete()

        # 🆕 Enviar email de confirmación
        try:
            from .emails import enviar_email_confirmacion_pedido
            enviar_email_confirmacion_pedido(pedido)
        except ImportError:
            print("⚠️ Módulo de emails no disponible")
        except Exception as e:
            print(f"⚠️ Error enviando email: {e}")

        messages.success(request, f'¡Pedido #{pedido.id} realizado con éxito! Total: ${pedido.total}')

        # 🔥 REDIRECCIÓN SEGÚN MÉTODO
        if metodo_pago == 'paypal':
            return redirect('pago_paypal', pedido_id=pedido.id)

        elif metodo_pago == 'tarjeta':
            return redirect('pago_stripe', pedido_id=pedido.id)

        elif metodo_pago == 'transferencia':
            return redirect('pago_azul', pedido_id=pedido.id)

        elif metodo_pago == 'efectivo':
            return redirect('pedido_exitoso')

        return redirect('pedido_exitoso')

    return render(request, 'carrito/checkout_moderno.html', {
        'items': items,
        'productos': items,
        'subtotal': sum(item.subtotal() for item in items),
        'total': sum(item.subtotal() for item in items) + 5,  # Envío estándar por defecto
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
    # Obtener TODOS los pedidos del usuario sin filtros
    todos_los_pedidos = Pedido.objects.all().order_by('-creado')
    pedidos_usuario = Pedido.objects.filter(usuario=request.user).order_by('-creado')
    
    # Debug: imprimir información detallada
    print("=" * 50)
    print("DEBUG - HISTORIAL DE PEDIDOS")
    print(f"Usuario actual: {request.user.username} (ID: {request.user.id})")
    print(f"Total de pedidos en DB: {todos_los_pedidos.count()}")
    print(f"Pedidos del usuario: {pedidos_usuario.count()}")
    
    # Mostrar todos los pedidos en DB
    print("\nTodos los pedidos en la base de datos:")
    for p in todos_los_pedidos:
        print(f"  Pedido #{p.id}: Usuario={p.usuario.username} (ID:{p.usuario.id}) - Estado={p.estado} - Total=${p.total} - Fecha={p.creado}")
    
    # Mostrar pedidos del usuario
    print(f"\nPedidos de {request.user.username}:")
    for p in pedidos_usuario:
        print(f"  Pedido #{p.id}: Estado={p.estado} - Total=${p.total} - Fecha={p.creado}")
    
    print("=" * 50)
    
    # Pre-cargar los items de cada pedido para optimizar
    pedidos = pedidos_usuario.prefetch_related('items__producto')

    return render(request, 'carrito/historial_moderno.html', {
        'pedidos': pedidos,
        'debug': True  # Forzar debug en el template
    })


@login_required
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    items = pedido.items.all()
    
    return render(request, 'carrito/detalle_pedido.html', {
        'pedido': pedido,
        'items': items
    })



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
        # Guardar el payment ID en el pedido
        pedido.metodo_pago = 'paypal'
        pedido.save()
        
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
@user_passes_test(lambda u: u.is_staff, login_url='/admin/login/')
def paypal_exito(request):
    """Procesar éxito de PayPal (solo admin)"""
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
    
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Verificación de seguridad: solo admin o dueño del pedido
    if pedido.usuario != request.user and not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a este pedido')
        return redirect('ver_carrito')
    
    # Ejecutar el pago
    payment = paypalrestsdk.Payment.find(payment_id)
    
    if payment.execute({"payer_id": payer_id}):
        # Pago exitoso - actualizar estado del pedido
        pedido.estado = 'pagado'
        pedido.save()
        
        messages.success(request, f'¡Pago del pedido #{pedido.id} confirmado con éxito!')
        return redirect('detalle_pedido', pedido_id=pedido.id)
    else:
        messages.error(request, 'Error al procesar el pago de PayPal')
        return redirect('detalle_pedido', pedido_id=pedido.id)


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='/admin/login/')
def paypal_cancelado(request):
    """Procesar cancelación de PayPal (solo admin)"""
    pedido_id = request.GET.get('pedido_id')
    
    if pedido_id:
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        # Verificación de seguridad: solo admin o dueño del pedido
        if pedido.usuario != request.user and not request.user.is_staff:
            messages.error(request, 'No tienes permiso para acceder a este pedido')
            return redirect('ver_carrito')
        
        messages.warning(request, f'Pago del pedido #{pedido.id} cancelado. Puedes intentarlo nuevamente.')
        return redirect('detalle_pedido', pedido_id=pedido.id)
    else:
        messages.warning(request, 'Pago cancelado')
        return redirect('historial_pedidos')




def pago_stripe(request, pedido_id):
    return render(request, 'carrito/pago_stripe.html', {'pedido_id': pedido_id})


def pago_azul(request, pedido_id):
    return render(request, 'carrito/pago_azul.html', {'pedido_id': pedido_id})

def paypal_cancelado(request):
    pedido_id = request.GET.get('pedido_id')
    
    if pedido_id:
        pedido = get_object_or_404(Pedido, id=pedido_id)
        messages.warning(request, f'Pago del pedido #{pedido.id} cancelado. Puedes intentarlo nuevamente.')
        return redirect('detalle_pedido', pedido_id=pedido.id)
    else:
        messages.warning(request, 'Pago cancelado')
        return redirect('historial_pedidos')