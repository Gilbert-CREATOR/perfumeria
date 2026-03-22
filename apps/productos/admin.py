from django.contrib import admin
from .models import Producto

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'precio', 'stock', 'disponible')
    list_filter = ('marca', 'tipo', 'temporada')
    search_fields = ('nombre', 'marca')