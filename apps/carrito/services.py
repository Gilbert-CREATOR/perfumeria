from django.db import transaction

from apps.productos.models import Producto

from .models import Carrito, ItemCarrito


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
