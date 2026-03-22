from django.urls import path
from . import admin_views

urlpatterns = [
    path('panel/', admin_views.admin_panel, name='admin_panel'),
    path('productos/', admin_views.admin_productos, name='admin_productos'),
    path('productos/nuevo/', admin_views.admin_producto_crear, name='admin_producto_crear'),
    path('productos/<int:producto_id>/editar/', admin_views.admin_producto_editar, name='admin_producto_editar'),
    path('productos/<int:producto_id>/eliminar/', admin_views.admin_producto_eliminar, name='admin_producto_eliminar'),
    path('productos/<int:producto_id>/toggle/', admin_views.admin_producto_toggle_disponibilidad, name='admin_producto_toggle_disponibilidad'),
    path('pedidos/', admin_views.admin_pedidos, name='admin_pedidos'),
    path('pedido/<int:pedido_id>/', admin_views.admin_detalle_pedido, name='admin_detalle_pedido'),
    path('analytics/', admin_views.admin_analytics, name='admin_analytics'),
    path('stock/', admin_views.admin_productos_stock, name='admin_stock'),
    path('envios/', admin_views.admin_envios, name='admin_envios'),
    path('envio/<int:envio_id>/', admin_views.admin_detalle_envio, name='admin_detalle_envio'),
    path('metodos-envio/', admin_views.admin_metodos_envio, name='admin_metodos_envio'),
    path('metodos-envio/<int:metodo_id>/editar/', admin_views.admin_metodo_envio_editar, name='admin_metodo_envio_editar'),
    path('metodos-envio/<int:metodo_id>/toggle/', admin_views.admin_metodo_envio_toggle, name='admin_metodo_envio_toggle'),
    path('metodos-envio/<int:metodo_id>/eliminar/', admin_views.admin_metodo_envio_eliminar, name='admin_metodo_envio_eliminar'),
    path('facturacion/', admin_views.admin_facturacion, name='admin_facturacion'),
    path('facturacion/exportar/', admin_views.admin_exportar_facturacion_csv, name='admin_exportar_facturacion_csv'),
]
