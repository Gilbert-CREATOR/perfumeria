from django.contrib import admin
from .models import Carrito, ItemCarrito, Pedido, ItemPedido

admin.site.register(Carrito)
admin.site.register(ItemCarrito)
admin.site.register(Pedido)
admin.site.register(ItemPedido)