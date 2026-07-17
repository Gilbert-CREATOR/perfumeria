from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.productos.models import Producto

from .models import Carrito, ItemCarrito, ItemPedido, MovimientoInventario, Pedido


PENDING_CART_SESSION_KEY = 'pending_cart_item'


def add_product_to_cart(user, product_id, quantity=1):
    """Añade una cantidad al carrito validando el stock de forma atómica."""
    try:
        quantity = max(1, int(quantity))
    except (TypeError, ValueError):
        quantity = 1

    with transaction.atomic():
        try:
            producto = Producto.objects.select_for_update().get(pk=product_id)
        except Producto.DoesNotExist:
            return False, 'El producto ya no está disponible.'

        carrito, _created = Carrito.objects.get_or_create(usuario=user)
        item, created = ItemCarrito.objects.get_or_create(
            carrito=carrito,
            producto=producto,
            defaults={'cantidad': 0},
        )
        new_quantity = item.cantidad + quantity

        if not producto.validar_stock(new_quantity):
            if created:
                item.delete()
            if producto.stock <= 0 or not producto.disponible:
                return False, 'Este producto no tiene stock disponible.'
            return False, f'Stock insuficiente. Solo quedan {producto.stock} unidades.'

        item.cantidad = new_quantity
        item.save(update_fields=['cantidad'])

    if quantity == 1:
        return True, f'{producto.nombre} agregado al carrito.'
    return True, f'{quantity} unidades de {producto.nombre} agregadas al carrito.'


def save_pending_cart_item(request, product_id, quantity):
    request.session[PENDING_CART_SESSION_KEY] = {
        'product_id': int(product_id),
        'quantity': max(1, int(quantity)),
    }
    request.session.modified = True


def complete_pending_cart_item(request):
    """Consume la acción pendiente únicamente después de autenticar al usuario."""
    if not request.user.is_authenticated:
        return None

    pending = request.session.pop(PENDING_CART_SESSION_KEY, None)
    if not pending:
        return None

    request.session.modified = True
    return add_product_to_cart(
        request.user,
        pending.get('product_id'),
        pending.get('quantity', 1),
    )


class CheckoutError(Exception):
    pass


def crear_pedido_desde_carrito(*, usuario, metodo_envio, metodo_pago, datos_envio):
    """Crea un pedido y reserva stock en una única transacción."""
    with transaction.atomic():
        carrito = Carrito.objects.select_for_update().get(usuario=usuario)
        items = list(carrito.items.select_related('producto').order_by('id'))
        if not items:
            raise CheckoutError('Tu carrito está vacío.')

        product_ids = [item.producto_id for item in items]
        productos = {
            producto.pk: producto
            for producto in Producto.objects.select_for_update().filter(pk__in=product_ids)
        }
        for item in items:
            producto = productos.get(item.producto_id)
            if not producto or not producto.validar_stock(item.cantidad):
                disponible = producto.stock if producto else 0
                nombre = producto.nombre if producto else 'el producto'
                raise CheckoutError(
                    f'Stock insuficiente para {nombre}. Solo quedan {disponible} unidades.'
                )

        subtotal = sum(
            (Decimal(str(productos[item.producto_id].precio)) * item.cantidad for item in items),
            Decimal('0.00'),
        )
        costo_envio = Decimal(str(metodo_envio.costo))
        pedido = Pedido.objects.create(
            usuario=usuario,
            metodo_pago=metodo_pago,
            subtotal=subtotal,
            costo_envio=costo_envio,
            total=subtotal + costo_envio,
            stock_reservado=True,
            reserva_expira_en=(
                timezone.now() + timedelta(minutes=30)
                if metodo_pago == 'paypal' else None
            ),
            **datos_envio,
        )

        for item in items:
            producto = productos[item.producto_id]
            ItemPedido.objects.create(
                pedido=pedido,
                producto=producto,
                nombre_producto=producto.nombre,
                marca_producto=producto.marca,
                cantidad=item.cantidad,
                precio=producto.precio,
            )
            Producto.objects.filter(pk=producto.pk).update(stock=F('stock') - item.cantidad)
            MovimientoInventario.objects.create(
                producto=producto,
                producto_nombre=producto.nombre,
                pedido=pedido,
                usuario=usuario,
                tipo='reserva',
                cantidad=-item.cantidad,
                stock_anterior=producto.stock,
                stock_resultante=producto.stock - item.cantidad,
                motivo=f'Reserva automatica para el pedido #{pedido.pk}',
            )

        from .models import Envio
        Envio.objects.create(pedido=pedido, metodo_envio=metodo_envio)
        carrito.items.all().delete()
        return pedido


def reintegrar_stock_pedido(pedido):
    """Devuelve una reserva exactamente una vez."""
    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(pk=pedido.pk)
        if not pedido.stock_reservado or pedido.stock_reintegrado:
            return False
        product_ids = [
            item.producto_id for item in pedido.items.all() if item.producto_id
        ]
        productos = {
            producto.pk: producto
            for producto in Producto.objects.select_for_update().filter(pk__in=product_ids)
        }
        for item in pedido.items.all():
            if item.producto_id:
                producto = productos.get(item.producto_id)
                if not producto:
                    continue
                stock_anterior = producto.stock
                producto.stock += item.cantidad
                producto.save(update_fields=['stock'])
                MovimientoInventario.objects.create(
                    producto=producto,
                    producto_nombre=item.nombre_visible,
                    pedido=pedido,
                    tipo='reintegro',
                    cantidad=item.cantidad,
                    stock_anterior=stock_anterior,
                    stock_resultante=producto.stock,
                    motivo=f'Reintegro del pedido #{pedido.pk}',
                )
        pedido.stock_reintegrado = True
        pedido.stock_reservado = False
        pedido.save(update_fields=['stock_reintegrado', 'stock_reservado', 'actualizado'])
        return True


def confirmar_pago(pedido, *, referencia=''):
    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(pk=pedido.pk)
        if pedido.estado == 'pagado':
            return pedido, False
        if pedido.stock_reintegrado:
            raise CheckoutError('La reserva de inventario de este pedido ya venció.')
        if pedido.reserva_expira_en and pedido.reserva_expira_en <= timezone.now():
            raise CheckoutError('La reserva de inventario de este pedido ya venció.')
        pedido.estado = 'pagado'
        pedido.pagado_en = timezone.now()
        pedido.reserva_expira_en = None
        if referencia:
            pedido.referencia_pago = referencia
        pedido.save(update_fields=[
            'estado', 'pagado_en', 'reserva_expira_en', 'referencia_pago', 'actualizado',
        ])
        return pedido, True


def liberar_reservas_vencidas(*, limite=100):
    """Libera reservas vencidas; es seguro ejecutarlo repetidamente."""
    ids = list(Pedido.objects.filter(
        estado='pendiente',
        stock_reservado=True,
        stock_reintegrado=False,
        reserva_expira_en__lte=timezone.now(),
    ).order_by('id').values_list('id', flat=True)[:limite])
    liberados = 0
    for pedido in Pedido.objects.filter(pk__in=ids):
        if reintegrar_stock_pedido(pedido):
            Pedido.objects.filter(pk=pedido.pk, estado='pendiente').update(estado='cancelado')
            liberados += 1
    return liberados
