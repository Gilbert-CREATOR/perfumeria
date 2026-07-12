from django.shortcuts import render


def home(request):
    from apps.productos.models import Producto

    productos_destacados = Producto.objects.filter(disponible=True)[:6]
    return render(request, 'home.html', {'productos_destacados': productos_destacados})
