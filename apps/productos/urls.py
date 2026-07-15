from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('productos/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('productos/<int:producto_id>/imagen/', views.producto_imagen, name='producto_imagen'),
    path('productos/<int:producto_id>/alerta-stock/', views.crear_alerta_stock, name='crear_alerta_stock'),
    path('productos/<int:producto_id>/resena/', views.crear_resena, name='crear_resena'),
    path('productos/api/quick-preview/<int:producto_id>/', views.quick_preview_api, name='quick_preview_api'),
    path('favorito/<int:producto_id>/', views.toggle_favorito, name='toggle_favorito'),
    path('favoritos/', views.ver_favoritos, name='ver_favoritos'),
    path('buscar-ajax/', views.buscar_ajax, name='buscar_ajax'),
]
