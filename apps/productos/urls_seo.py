from django.urls import path
from . import views

urlpatterns = [
    # URLs amigables para productos
    path('perfume/<slug:slug>/', views.detalle_producto_seo, name='detalle_producto_seo'),
    
    # URLs de categorías
    path('categoria/<slug:categoria>/', views.catalogo_seo, name='catalogo_categoria'),
    path('marca/<slug:marca>/', views.catalogo_seo, name='catalogo_marca'),
    
    # Sitemap
    path('sitemap.xml', views.sitemap, name='sitemap'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
]
