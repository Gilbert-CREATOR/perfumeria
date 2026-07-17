from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.conf import settings
from django.views.static import serve
from apps.core import views as core_views

urlpatterns = [
    # 🎯 URLs principales
    path('', include('apps.productos.urls')),
    path('', include('apps.productos.urls_seo')),
    path('carrito/', include('apps.carrito.urls')),
    path('usuarios/', include('apps.usuarios.urls')),
    path('newsletter/', include('apps.newsletter.urls')),

    # 🎯 URLs del panel admin personalizado
    path('admin/', include('apps.carrito.admin_urls')),
    
    # 📄 Páginas estáticas
    path('contacto/', core_views.contacto, name='contacto'),
    path('nosotros/', core_views.nosotros, name='nosotros'),
    path('faq/', core_views.faq, name='faq'),
    path('blog/', core_views.blog, name='blog'),
    path('blog/<slug:slug>/', core_views.articulo_blog, name='articulo_blog'),
    
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
