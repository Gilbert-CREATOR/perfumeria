from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .models import ArticuloBlog, ConfiguracionSitio, MensajeContacto, PreguntaFrecuente
from django.shortcuts import get_object_or_404


def home(request):
    from apps.productos.models import Producto

    productos_destacados = Producto.objects.filter(disponible=True)[:6]
    return render(request, 'home.html', {'productos_destacados': productos_destacados})


@require_http_methods(['GET', 'POST'])
def contacto(request):
    if request.method == 'POST':
        datos = {
            'nombre': request.POST.get('nombre', '').strip(),
            'email': request.POST.get('email', '').strip().lower(),
            'telefono': request.POST.get('telefono', '').strip(),
            'asunto': request.POST.get('asunto', '').strip(),
            'mensaje': request.POST.get('mensaje', '').strip(),
            'urgente': request.POST.get('urgente') == 'on',
        }
        if not all(datos[key] for key in ('nombre', 'email', 'asunto', 'mensaje')) or '@' not in datos['email']:
            messages.error(request, 'Completa correctamente los campos obligatorios.')
        else:
            MensajeContacto.objects.create(**datos)
            messages.success(request, 'Recibimos tu mensaje. Nuestro equipo se pondrá en contacto contigo.')
            return redirect('contacto')
    return render(request, 'pages/contacto.html')


def nosotros(request):
    return render(request, 'pages/nosotros.html')


def faq(request):
    preguntas = PreguntaFrecuente.objects.filter(activa=True)
    return render(request, 'pages/faq.html', {'preguntas_frecuentes': preguntas})


def blog(request):
    articulos = ArticuloBlog.objects.filter(publicado=True, publicado_en__isnull=False)
    return render(request, 'pages/blog.html', {'articulos': articulos})


def articulo_blog(request, slug):
    articulo = get_object_or_404(ArticuloBlog, slug=slug, publicado=True)
    return render(request, 'pages/articulo_blog.html', {'articulo': articulo})
