from django.urls import path
from . import views
from . import views_debug
from . import admin_views_extra
from . import empleado_views

urlpatterns = [
    # Rutas públicas (clientes)
    path('', views.ver_carrito, name='ver_carrito'),
    path('agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('eliminar/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('disminuir/<int:item_id>/', views.disminuir_cantidad, name='disminuir_cantidad'),
    path('checkout/', views.checkout, name='checkout'),
    path('exito/', views.pedido_exitoso, name='pedido_exitoso'),
    path('historial/', views.historial_pedidos, name='historial_pedidos'),
    path('pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    
    # Rutas de pago (clientes) - pero protegidas
    path('pago/paypal/<int:pedido_id>/', views.pago_paypal, name='pago_paypal'),
    path('pago/stripe/<int:pedido_id>/', views.pago_stripe, name='pago_stripe'),
    path('pago/azul/<int:pedido_id>/', views.pago_azul, name='pago_azul'),
    
    # Rutas de administrador (solo admin)
    path('admin/usuarios/', admin_views_extra.admin_usuarios, name='admin_usuarios'),
    path('admin/pedidos/', admin_views_extra.admin_pedidos_todos, name='admin_pedidos_todos'),
    path('admin/usuario/<int:user_id>/pedidos/', admin_views_extra.admin_usuario_pedidos, name='admin_usuario_pedidos'),
    path('admin/estadisticas/', admin_views_extra.admin_estadisticas, name='admin_estadisticas'),
    path('admin/paypal/success/', views.paypal_exito, name='paypal_exito'),  # Movido a admin
    path('admin/paypal/cancel/', views.paypal_cancelado, name='paypal_cancelado'),  # Movido a admin
    path('debug/', views_debug.debug_pedidos, name='debug_pedidos'),
    
    # Rutas de empleados (admin y empleados)
    path('empleados/', empleado_views.empleados_lista, name='empleados_lista'),
    path('empleados/agregar/', empleado_views.agregar_empleado, name='agregar_empleado'),
    path('empleados/editar/<int:user_id>/', empleado_views.editar_empleado, name='editar_empleado'),
    path('empleados/eliminar/<int:user_id>/', empleado_views.eliminar_empleado, name='eliminar_empleado'),
    path('panel/', empleado_views.panel_empleado, name='panel_empleado'),
    
    # API endpoints (públicos pero seguros)
    path('api/count/', views.api_cart_count, name='api_cart_count'),
]