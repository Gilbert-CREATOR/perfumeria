from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    # 🎯 URLs principales
    path('', include('apps.productos.urls')),
    path('carrito/', include('apps.carrito.urls')),
    path('usuarios/', include('apps.usuarios.urls')),

    # 🎯 URLs del panel admin personalizado
    path('admin/', include('apps.carrito.admin_urls')),
    
    # 📄 Páginas estáticas
    path('contacto/', TemplateView.as_view(template_name='pages/contacto.html'), name='contacto'),
    path('nosotros/', TemplateView.as_view(template_name='pages/nosotros.html'), name='nosotros'),
    path('faq/', TemplateView.as_view(template_name='pages/faq.html'), name='faq'),
    
    # 🚫 Error pages
    path('404/', TemplateView.as_view(template_name='404_moderno.html'), name='404'),
]

# 🖼️ Servir media files en desarrollo y producción
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # En producción, servir media files con WhiteNoise
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # 🖼️ Asegurar que media files se sirvan en producción
    from django.views.static import serve
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
