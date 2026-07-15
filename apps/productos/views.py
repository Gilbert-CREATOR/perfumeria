from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
import base64
import binascii
from django.db.models import Q, Count
from django.db.models.functions import Lower
from .models import Producto, Favorito, AlertaStock, Resena
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect
from .forms import ResenaForm
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import ensure_csrf_cookie

def format_price(price):
    """Formatear precio para que sea más legible"""
    if price:
        return f"${price:,.0f}".replace(",", ",")
    return "$0"


def catalog_season_options():
    """Devuelve las seis temporadas oficiales en su orden visual."""
    return [(value, label.upper()) for value, label in Producto.TEMPORADA_CHOICES]


def sort_catalog_products(productos, sort):
    """Aplica un orden estable a los productos del catálogo."""
    if sort == 'nombre':
        return productos.order_by(Lower('nombre'), 'id')
    if sort == 'precio_asc':
        return productos.order_by('precio', 'id')
    if sort == 'precio_desc':
        return productos.order_by('-precio', 'id')
    if sort == 'popularidad':
        return productos.annotate(resena_count=Count('resenas')).order_by('-resena_count', 'id')
    return productos

@ensure_csrf_cookie
def catalogo(request):
    productos = Producto.objects.filter(disponible=True).prefetch_related('resenas').order_by('id')

    # 🔍 BUSCADOR
    query = request.GET.get('q')
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(marca__icontains=query)
        )

    # 🔥 FILTRO POR TEMPORADA
    temporada = request.GET.get('temporada')
    if temporada:
        productos = productos.filter(temporada__contains=[temporada])

    # 🆕 FILTROS AVANZADOS
    marca = request.GET.get('marca')
    if marca:
        productos = productos.filter(marca__icontains=marca)

    precio_min = request.GET.get('precio_min')
    if precio_min:
        productos = productos.filter(precio__gte=precio_min)

    precio_max = request.GET.get('precio_max')
    if precio_max:
        productos = productos.filter(precio__lte=precio_max)

    # 🌸 FILTROS POR NOTAS OLFACTIVAS (simulado por temporada/tipo)
    notas = request.GET.get('notas')
    if notas:
        notas_array = notas.split(',')
        # Mapear notas a tipos/temporadas
        notas_mapping = {
            'citrico': ['verano', 'dia'],
            'floral': ['primavera', 'dia'],
            'madera': ['invierno', 'noche'],
            'oriental': ['noche', 'otono'],
            'fresco': ['dia', 'verano'],
            'dulce': ['otono', 'noche']
        }
        
        notas_filter = Q()
        for nota in notas_array:
            if nota in notas_mapping:
                for temp in notas_mapping[nota]:
                    notas_filter |= Q(temporada__contains=[temp])
        
        productos = productos.filter(notas_filter)

    # 💪 FILTRO POR INTENSIDAD (simulado por tipo)
    intensidad = request.GET.get('intensidad')
    if intensidad:
        intensidad_mapping = {
            'ligero': ['eau_de_cologne', 'body_spray'],
            'medio': ['eau_de_toilette'],
            'intenso': ['eau_de_parfum']
        }
        
        if intensidad in intensidad_mapping:
            productos = productos.filter(tipo__in=intensidad_mapping[intensidad])

    # 🎯 FILTRO POR OCASIÓN (simulado por temporada)
    ocasion = request.GET.get('ocasion')
    if ocasion:
        ocasiones_array = ocasion.split(',')
        ocasion_mapping = {
            'diario': ['dia'],
            'trabajo': ['dia'],
            'noche': ['noche'],
            'especial': ['otono', 'noche'],
            'romantico': ['noche', 'primavera'],
            'deportivo': ['dia', 'verano']
        }
        
        ocasion_filter = Q()
        for oc in ocasiones_array:
            if oc in ocasion_mapping:
                for temp in ocasion_mapping[oc]:
                    ocasion_filter |= Q(temporada__contains=[temp])
        
        productos = productos.filter(ocasion_filter)

    # 📊 ORDENAMIENTO
    sort = request.GET.get('sort')
    productos = sort_catalog_products(productos, sort)

    # 📄 PAGINACIÓN
    paginator = Paginator(productos, 12)
    page_number = request.GET.get('page')
    productos = paginator.get_page(page_number)

    # 🏷️ MARCAS ÚNICAS
    marcas = list(
        Producto.objects.exclude(marca='')
        .values_list('marca', flat=True)
        .distinct()
        .order_by('marca')
    )

    temporadas_catalogo = catalog_season_options()
    
    # 📊 CONTADORES POR TEMPORADA
    temporada_contadores = {}
    for temporada, _label in Producto.TEMPORADA_CHOICES:
        temporada_contadores[temporada] = Producto.objects.filter(
            temporada__contains=[temporada],
            disponible=True
        ).count()

    context = {
        'productos': productos,
        'paginator': paginator,
        'marcas': marcas,
        'temporadas_catalogo': temporadas_catalogo,
        'total_productos': paginator.count,
        'temporada_contadores': temporada_contadores,
    }
    return render(request, 'catalogo/catalogo.html', context)

@ensure_csrf_cookie
def home(request):
    """Vista principal con productos destacados"""
    productos_destacados = Producto.objects.filter(disponible=True)[:6]
    productos_recomendados = Producto.objects.filter(disponible=True)[:4]
    
    context = {
        'productos_destacados': productos_destacados,
        'productos_recomendados': productos_recomendados,
    }
    return render(request, 'home.html', context)

@ensure_csrf_cookie
def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto.objects.prefetch_related('resenas__usuario'), id=producto_id)
    resenas = producto.resenas.select_related('usuario').order_by('-creado')
    
    # Productos relacionados
    productos_relacionados = Producto.objects.filter(
        disponible=True, 
        marca=producto.marca
    ).exclude(id=producto.id)[:4]

    context = {
        'producto': producto,
        'resenas': resenas,
        'productos_relacionados': productos_relacionados,
        'alerta_stock_activa': (
            request.user.is_authenticated
            and AlertaStock.objects.filter(usuario=request.user, producto=producto, enviada__isnull=True).exists()
        ),
        'puede_resenar': (
            request.user.is_authenticated
            and request.user.pedido_set.filter(items__producto=producto, estado='entregado').exists()
        ),
        'resena_form': ResenaForm(),
    }
    return render(request, 'productos/detalle_producto_minimalista.html', context)


@login_required
def crear_alerta_stock(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        if producto.stock > 0:
            messages.info(request, 'Este producto ya está disponible.')
        else:
            alerta, created = AlertaStock.objects.get_or_create(
                usuario=request.user,
                producto=producto,
                defaults={'enviada': None},
            )
            if not created and alerta.enviada:
                alerta.enviada = None
                alerta.save(update_fields=['enviada'])
            messages.success(request, 'Te avisaremos por correo cuando vuelva a estar disponible.')
    return redirect(f'{reverse("detalle_producto", args=[producto.id])}#disponibilidad')


@login_required
def crear_resena(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    compro_producto = request.user.pedido_set.filter(
        items__producto=producto,
        estado='entregado',
    ).exists()
    if request.method != 'POST' or not compro_producto:
        messages.error(request, 'Solo puedes reseñar productos de pedidos entregados.')
        return redirect(f'{reverse("detalle_producto", args=[producto.id])}#resena')

    form = ResenaForm(request.POST)
    if form.is_valid():
        resena = Resena.objects.filter(usuario=request.user, producto=producto).order_by('id').first()
        if resena:
            resena.comentario = form.cleaned_data['comentario']
            resena.estrellas = form.cleaned_data['estrellas']
            resena.save(update_fields=['comentario', 'estrellas'])
        else:
            Resena.objects.create(
                usuario=request.user,
                producto=producto,
                comentario=form.cleaned_data['comentario'],
                estrellas=form.cleaned_data['estrellas'],
            )
        messages.success(request, 'Gracias por compartir tu experiencia.')
    else:
        messages.error(request, 'Revisa la puntuación y el comentario.')
    return redirect(f'{reverse("detalle_producto", args=[producto.id])}#resena')

@login_required
def toggle_favorito(request, producto_id):
    """Toggle favorito para un producto"""
    producto = get_object_or_404(Producto, id=producto_id)
    favorito, created = Favorito.objects.get_or_create(
        usuario=request.user,
        producto=producto
    )
    
    if not created:
        favorito.delete()
        return JsonResponse({'success': True, 'is_favorito': False})
    
    return JsonResponse({'success': True, 'is_favorito': True})

@login_required
def ver_favoritos(request):
    """Ver lista de favoritos del usuario"""
    favoritos = Favorito.objects.filter(usuario=request.user).select_related('producto')
    
    context = {
        'favoritos': favoritos,
    }
    return render(request, 'productos/favoritos_moderno.html', context)

def quick_preview_api(request, producto_id):
    """API para obtener datos del producto para Quick Preview"""
    try:
        producto = get_object_or_404(Producto.objects.prefetch_related('resenas'), id=producto_id)
        
        data = {
            'success': True,
            'product': {
                'id': producto.id,
                'nombre': producto.nombre,
                'marca': producto.marca,
                'precio': str(producto.precio),
                'tamano_ml': producto.tamano_ml,
                'descripcion': producto.descripcion,
                'tipo_display': producto.get_tipo_display(),
                'temporada_display': producto.get_temporada_display() or 'Todas',
                'stock': producto.stock,
                'imagen': producto.imagen.url if producto.imagen else None,
                'rating_promedio': producto.rating_promedio(),
                'total_resenas': producto.total_resenas(),
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def buscar_ajax(request):
    """Búsqueda AJAX para productos"""
    query = request.GET.get('q', '')
    productos = Producto.objects.filter(
        disponible=True,
        nombre__icontains=query
    )[:10]
    
    results = []
    for producto in productos:
        results.append({
            'id': producto.id,
            'nombre': producto.nombre,
            'marca': producto.marca,
            'precio': str(producto.precio),
            'imagen': producto.imagen.url if producto.imagen else None,
        })
    
    return JsonResponse({'results': results})


def producto_imagen(request, producto_id):
    """Sirve la copia persistente de la imagen guardada en PostgreSQL."""
    producto = get_object_or_404(Producto, id=producto_id)
    if not producto.imagen_base64:
        return HttpResponse(status=404)

    try:
        contenido = base64.b64decode(producto.imagen_base64, validate=True)
    except (ValueError, binascii.Error):
        return HttpResponse(status=404)

    response = HttpResponse(contenido, content_type=producto.imagen_content_type())
    response['Cache-Control'] = 'public, max-age=86400'
    response['Content-Disposition'] = f'inline; filename="{producto.imagen_nombre or "producto.jpg"}"'
    return response
