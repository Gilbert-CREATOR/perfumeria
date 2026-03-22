def carrito_total(request):
    if request.user.is_authenticated:
        try:
            from .models import Carrito
            from django.db.models import Sum
            carrito, created = Carrito.objects.get_or_create(usuario=request.user)
            total_items = carrito.items.aggregate(total=Sum('cantidad'))['total'] or 0
        except:
            total_items = 0
    else:
        total_items = 0

    return {
        'carrito_count': total_items,
        'total_items_carrito': total_items
    }