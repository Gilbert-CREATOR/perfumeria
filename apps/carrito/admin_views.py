from functools import wraps
import csv
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import DecimalField, F, Q, Sum
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.productos.models import Producto
from .admin_forms import EnvioForm, MetodoEnvioForm, PedidoAdminForm, ProductoAdminForm
from .models import ESTADOS_PEDIDO, Envio, ItemPedido, MetodoEnvio, Pedido

ADMIN_LOGIN_URL = '/usuarios/login/'
PEDIDO_ESTADOS_COBRADOS = ['pagado', 'enviado', 'entregado']


def es_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def admin_required(view_func):
    @wraps(view_func)
    @login_required(login_url=ADMIN_LOGIN_URL)
    @user_passes_test(es_admin, login_url=ADMIN_LOGIN_URL)
    def wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return wrapped_view


def parse_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {'1', 'true', 'on', 'yes', 'si'}


def count_by_choices(queryset, field_name, choices):
    return {
        key: queryset.filter(**{field_name: key}).count()
        for key, _label in choices
    }


def shift_month(date_value, delta):
    month_index = date_value.month - 1 + delta
    year = date_value.year + month_index // 12
    month = month_index % 12 + 1
    return date_value.replace(year=year, month=month, day=1)


@admin_required
def admin_panel(request):
    hoy = timezone.localdate()
    inicio_mes = hoy.replace(day=1)

    pedidos = Pedido.objects.all()
    pedidos_pagados = pedidos.filter(estado__in=PEDIDO_ESTADOS_COBRADOS)
    pedidos_recientes = pedidos.select_related('usuario').order_by('-creado')[:8]
    productos_bajo_stock = Producto.objects.filter(stock__gt=0, stock__lt=5).order_by('stock', 'nombre')[:6]
    pedidos_sin_envio = (
        Pedido.objects.select_related('usuario')
        .filter(estado__in=['pagado', 'enviado'], envio__isnull=True)
        .order_by('-creado')[:5]
    )

    stats = {
        'total_pedidos': pedidos.count(),
        'pedidos_hoy': pedidos.filter(creado__date=hoy).count(),
        'pedidos_mes': pedidos.filter(creado__date__gte=inicio_mes).count(),
        'ingresos_mes': pedidos_pagados.filter(creado__date__gte=inicio_mes).aggregate(
            total=Sum('total')
        )['total'] or 0,
        'pedidos_pendientes': pedidos.filter(estado='pendiente').count(),
        'productos_activos': Producto.objects.filter(disponible=True).count(),
        'stock_bajo': Producto.objects.filter(stock__gt=0, stock__lt=5).count(),
        'agotados': Producto.objects.filter(stock=0).count(),
        'envios_activos': Envio.objects.exclude(estado='entregado').count(),
    }

    return render(
        request,
        'admin_panel/dashboard_moderno.html',
        {
            'stats': stats,
            'pedidos_recientes': pedidos_recientes,
            'productos_bajo_stock': productos_bajo_stock,
            'pedidos_sin_envio': pedidos_sin_envio,
        },
    )


@admin_required
def admin_productos(request):
    productos = Producto.objects.all().order_by('-id')
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    tipo = request.GET.get('tipo', '').strip()

    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) |
            Q(marca__icontains=q) |
            Q(descripcion__icontains=q)
        )

    if tipo:
        productos = productos.filter(tipo=tipo)

    if estado == 'activos':
        productos = productos.filter(disponible=True)
    elif estado == 'inactivos':
        productos = productos.filter(disponible=False)
    elif estado == 'bajo_stock':
        productos = productos.filter(stock__gt=0, stock__lt=5)
    elif estado == 'agotados':
        productos = productos.filter(stock=0)

    stats = {
        'total': productos.count(),
        'activos': productos.filter(disponible=True).count(),
        'inactivos': productos.filter(disponible=False).count(),
        'bajo_stock': productos.filter(stock__gt=0, stock__lt=5).count(),
        'agotados': productos.filter(stock=0).count(),
    }

    return render(
        request,
        'admin_panel/productos.html',
        {
            'productos': productos,
            'producto_stats': stats,
            'estado_actual': estado,
            'tipo_actual': tipo,
            'busqueda': q,
            'tipos_producto': Producto.TIPO_CHOICES,
        },
    )


@admin_required
def admin_producto_crear(request):
    form = ProductoAdminForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        producto = form.save()
        messages.success(request, f'Producto "{producto.nombre}" creado correctamente.')
        return redirect('admin_productos')

    return render(
        request,
        'admin_panel/producto_form.html',
        {
            'form': form,
            'producto': None,
            'titulo': 'Nuevo producto',
            'descripcion': 'Crea un producto desde el panel administrativo.',
        },
    )


@admin_required
def admin_producto_editar(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    form = ProductoAdminForm(request.POST or None, request.FILES or None, instance=producto)

    if request.method == 'POST' and form.is_valid():
        producto = form.save()
        messages.success(request, f'Producto "{producto.nombre}" actualizado correctamente.')
        return redirect('admin_productos')

    return render(
        request,
        'admin_panel/producto_form.html',
        {
            'form': form,
            'producto': producto,
            'titulo': f'Editar {producto.nombre}',
            'descripcion': 'Actualiza la ficha comercial y el inventario base del producto.',
        },
    )


@admin_required
def admin_producto_eliminar(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == 'POST':
        if ItemPedido.objects.filter(producto=producto).exists():
            producto.disponible = False
            producto.save(update_fields=['disponible'])
            messages.warning(
                request,
                f'"{producto.nombre}" tiene historial de pedidos. Se desactivó en lugar de eliminarse.',
            )
        else:
            nombre = producto.nombre
            producto.delete()
            messages.success(request, f'Producto "{nombre}" eliminado correctamente.')

    return redirect('admin_productos')


@admin_required
def admin_producto_toggle_disponibilidad(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == 'POST':
        if not producto.disponible and producto.stock <= 0:
            messages.warning(request, f'No puedes activar "{producto.nombre}" con stock en 0.')
        else:
            producto.disponible = not producto.disponible
            producto.save(update_fields=['disponible'])
            estado = 'activo' if producto.disponible else 'inactivo'
            messages.success(request, f'"{producto.nombre}" ahora está {estado}.')

    return redirect('admin_productos')


@admin_required
def admin_pedidos(request):
    pedidos = Pedido.objects.select_related('usuario').order_by('-creado')
    estado = request.GET.get('estado', '').strip()
    q = request.GET.get('q', '').strip()

    if estado:
        pedidos = pedidos.filter(estado=estado)

    if q:
        criterio = (
            Q(usuario__username__icontains=q) |
            Q(usuario__email__icontains=q) |
            Q(nombre_completo__icontains=q) |
            Q(telefono__icontains=q)
        )
        if q.isdigit():
            criterio |= Q(id=int(q))
        pedidos = pedidos.filter(criterio)

    pedido_counts = count_by_choices(pedidos, 'estado', ESTADOS_PEDIDO)

    return render(
        request,
        'admin_panel/pedidos.html',
        {
            'pedidos': pedidos,
            'estado_actual': estado,
            'busqueda': q,
            'pedido_counts': pedido_counts,
            'estados_pedido': ESTADOS_PEDIDO,
        },
    )


@admin_required
def admin_detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(
        Pedido.objects.select_related('usuario').prefetch_related('items__producto'),
        id=pedido_id,
    )
    envio = getattr(pedido, 'envio', None)
    pedido_form = PedidoAdminForm(instance=pedido)
    envio_form = EnvioForm()
    metodos_activos = MetodoEnvio.objects.filter(activo=True)

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'actualizar_pedido':
            pedido_form = PedidoAdminForm(request.POST, instance=pedido)
            if pedido_form.is_valid():
                pedido_form.save()
                messages.success(request, f'Pedido #{pedido.id} actualizado correctamente.')
                return redirect('admin_detalle_pedido', pedido_id=pedido.id)
            messages.error(request, 'Revisa los datos del pedido antes de guardar.')

        elif accion == 'crear_envio':
            if envio:
                messages.info(request, f'El pedido #{pedido.id} ya tiene un envío creado.')
                return redirect('admin_detalle_envio', envio_id=envio.id)

            envio_form = EnvioForm(request.POST)
            if not metodos_activos.exists():
                messages.error(request, 'Primero crea o activa un método de envío.')
            elif envio_form.is_valid():
                nuevo_envio = envio_form.save(commit=False)
                nuevo_envio.pedido = pedido
                if nuevo_envio.estado in ['despachado', 'en_transito'] and not nuevo_envio.fecha_despacho:
                    nuevo_envio.fecha_despacho = timezone.now()
                if nuevo_envio.estado == 'entregado' and not nuevo_envio.fecha_entrega_real:
                    nuevo_envio.fecha_entrega_real = timezone.now()
                nuevo_envio.save()

                if nuevo_envio.estado == 'entregado':
                    pedido.estado = 'entregado'
                    pedido.save(update_fields=['estado'])
                elif nuevo_envio.estado in ['despachado', 'en_transito'] and pedido.estado in ['pendiente', 'pagado']:
                    pedido.estado = 'enviado'
                    pedido.save(update_fields=['estado'])

                messages.success(request, f'Se creó el envío del pedido #{pedido.id}.')
                return redirect('admin_detalle_envio', envio_id=nuevo_envio.id)
            else:
                messages.error(request, 'No se pudo crear el envío. Revisa el formulario.')

    return render(
        request,
        'admin_panel/detalle_pedido.html',
        {
            'pedido': pedido,
            'items': pedido.items.select_related('producto'),
            'pedido_form': pedido_form,
            'envio': envio,
            'envio_form': envio_form,
            'estados_pedido': ESTADOS_PEDIDO,
            'metodos_activos': metodos_activos,
        },
    )


@admin_required
def admin_analytics(request):
    inicio_mes_actual = timezone.localdate().replace(day=1)
    estadisticas_mensuales = []

    for delta in range(-5, 1):
        inicio_mes = shift_month(inicio_mes_actual, delta)
        inicio_mes_siguiente = shift_month(inicio_mes, 1)
        pedidos_mes = Pedido.objects.filter(
            creado__date__gte=inicio_mes,
            creado__date__lt=inicio_mes_siguiente,
        )
        ingresos_mes = pedidos_mes.filter(estado__in=PEDIDO_ESTADOS_COBRADOS).aggregate(
            total=Sum('total')
        )['total'] or 0

        estadisticas_mensuales.append(
            {
                'mes': inicio_mes.strftime('%b %Y'),
                'pedidos': pedidos_mes.count(),
                'ingresos': ingresos_mes,
            }
        )

    top_productos = (
        ItemPedido.objects.values('producto__nombre', 'producto__marca')
        .annotate(
            total_vendido=Sum('cantidad'),
            ingresos=Sum(
                F('cantidad') * F('precio'),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )
        .order_by('-total_vendido')[:10]
    )

    distribucion_estados = [
        {
            'label': label,
            'cantidad': Pedido.objects.filter(estado=estado).count(),
        }
        for estado, label in ESTADOS_PEDIDO
    ]

    resumen = {
        'ingresos_totales': Pedido.objects.filter(estado__in=PEDIDO_ESTADOS_COBRADOS).aggregate(
            total=Sum('total')
        )['total'] or 0,
        'clientes_unicos': Pedido.objects.values('usuario').distinct().count(),
        'productos_vendidos': ItemPedido.objects.aggregate(total=Sum('cantidad'))['total'] or 0,
        'ticket_promedio': Pedido.objects.filter(estado__in=PEDIDO_ESTADOS_COBRADOS).aggregate(
            promedio=Sum('total')
        )['promedio'] or 0,
    }

    pedidos_pagados = Pedido.objects.filter(estado__in=PEDIDO_ESTADOS_COBRADOS)
    if pedidos_pagados.exists():
        resumen['ticket_promedio'] = resumen['ingresos_totales'] / pedidos_pagados.count()

    return render(
        request,
        'admin_panel/analytics.html',
        {
        'estadisticas_mensuales': estadisticas_mensuales,
        'top_productos': top_productos,
        'distribucion_estados': distribucion_estados,
        'resumen': resumen,
        },
    )


@admin_required
def admin_productos_stock(request):
    productos = Producto.objects.all().order_by('stock', 'nombre')
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()

    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=request.POST.get('producto_id'))
        accion = request.POST.get('accion')

        if accion == 'actualizar_stock':
            try:
                nuevo_stock = int(request.POST.get('stock', producto.stock))
            except (TypeError, ValueError):
                messages.error(request, 'El stock debe ser un numero entero.')
            else:
                if nuevo_stock < 0:
                    messages.error(request, 'El stock no puede ser negativo.')
                else:
                    producto.stock = nuevo_stock
                    if nuevo_stock == 0:
                        producto.disponible = False
                    elif 'disponible' in request.POST:
                        producto.disponible = parse_bool(request.POST.get('disponible'))
                    producto.save()
                    messages.success(request, f'Stock de "{producto.nombre}" actualizado.')

        elif accion == 'toggle_disponibilidad':
            if not producto.disponible and producto.stock <= 0:
                messages.warning(request, f'No puedes activar "{producto.nombre}" con stock en 0.')
            else:
                producto.disponible = not producto.disponible
                producto.save(update_fields=['disponible'])
                estado_producto = 'activo' if producto.disponible else 'inactivo'
                messages.success(request, f'"{producto.nombre}" ahora está {estado_producto}.')

        return redirect('admin_stock')

    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) |
            Q(marca__icontains=q)
        )

    if estado == 'disponible':
        productos = productos.filter(disponible=True, stock__gt=0)
    elif estado == 'agotado':
        productos = productos.filter(stock=0)
    elif estado == 'bajo_stock':
        productos = productos.filter(stock__gt=0, stock__lt=5)
    elif estado == 'inactivo':
        productos = productos.filter(disponible=False)

    bajo_stock = productos.filter(stock__gt=0, stock__lt=5)
    agotados = productos.filter(stock=0)

    return render(
        request,
        'admin_panel/stock.html',
        {
            'productos': productos,
            'bajo_stock': bajo_stock,
            'agotados': agotados,
            'busqueda': q,
            'estado_actual': estado,
        },
    )


@admin_required
def admin_envios(request):
    envios = Envio.objects.select_related('pedido__usuario', 'metodo_envio').order_by('-creado')
    estado = request.GET.get('estado', '').strip()
    q = request.GET.get('q', '').strip()

    if estado:
        envios = envios.filter(estado=estado)

    if q:
        criterio = (
            Q(numero_seguimiento__icontains=q) |
            Q(pedido__usuario__username__icontains=q) |
            Q(pedido__usuario__email__icontains=q) |
            Q(metodo_envio__nombre__icontains=q)
        )
        if q.isdigit():
            criterio |= Q(pedido__id=int(q))
        envios = envios.filter(criterio)

    envio_counts = count_by_choices(envios, 'estado', Envio.ESTADO_ENVIO)
    pedidos_sin_envio = (
        Pedido.objects.select_related('usuario')
        .filter(estado__in=['pagado', 'enviado'], envio__isnull=True)
        .order_by('-creado')[:6]
    )

    return render(
        request,
        'admin_panel/envios.html',
        {
            'envios': envios,
            'estado_actual': estado,
            'busqueda': q,
            'envio_counts': envio_counts,
            'pedidos_sin_envio': pedidos_sin_envio,
            'estado_envio_choices': Envio.ESTADO_ENVIO,
        },
    )


@admin_required
def admin_detalle_envio(request, envio_id):
    envio = get_object_or_404(
        Envio.objects.select_related('pedido__usuario', 'metodo_envio'),
        id=envio_id,
    )
    form = EnvioForm(request.POST or None, instance=envio)

    if request.method == 'POST':
        if form.is_valid():
            envio = form.save(commit=False)
            if envio.estado in ['despachado', 'en_transito'] and not envio.fecha_despacho:
                envio.fecha_despacho = timezone.now()
            if envio.estado == 'entregado' and not envio.fecha_entrega_real:
                envio.fecha_entrega_real = timezone.now()
            envio.save()

            pedido = envio.pedido
            if envio.estado == 'entregado' and pedido.estado != 'entregado':
                pedido.estado = 'entregado'
                pedido.save(update_fields=['estado'])
            elif envio.estado in ['despachado', 'en_transito'] and pedido.estado in ['pendiente', 'pagado']:
                pedido.estado = 'enviado'
                pedido.save(update_fields=['estado'])

            messages.success(request, f'Envío del pedido #{pedido.id} actualizado.')
            return redirect('admin_detalle_envio', envio_id=envio.id)

        messages.error(request, 'No se pudo actualizar el envío. Revisa el formulario.')

    return render(
        request,
        'admin_panel/detalle_envio.html',
        {
            'envio': envio,
            'form': form,
        },
    )


@admin_required
def admin_metodos_envio(request):
    metodos = MetodoEnvio.objects.all().order_by('nombre')
    q = request.GET.get('q', '').strip()
    form = MetodoEnvioForm(request.POST or None)

    if q:
        metodos = metodos.filter(
            Q(nombre__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(tiempo_entrega__icontains=q)
        )

    if request.method == 'POST' and form.is_valid():
        metodo = form.save()
        messages.success(request, f'Método de envío "{metodo.nombre}" creado correctamente.')
        return redirect('admin_metodos_envio')

    stats = {
        'total': metodos.count(),
        'activos': metodos.filter(activo=True).count(),
        'inactivos': metodos.filter(activo=False).count(),
        'usados': Envio.objects.values('metodo_envio').distinct().count(),
    }

    return render(
        request,
        'admin_panel/metodos_envio.html',
        {
            'metodos': metodos,
            'form': form,
            'busqueda': q,
            'metodo_stats': stats,
        },
    )


@admin_required
def admin_metodo_envio_editar(request, metodo_id):
    metodo = get_object_or_404(MetodoEnvio, id=metodo_id)
    form = MetodoEnvioForm(request.POST or None, instance=metodo)

    if request.method == 'POST' and form.is_valid():
        metodo = form.save()
        messages.success(request, f'Método "{metodo.nombre}" actualizado correctamente.')
        return redirect('admin_metodos_envio')

    return render(
        request,
        'admin_panel/metodo_envio_form.html',
        {
            'form': form,
            'metodo': metodo,
        },
    )


@admin_required
def admin_metodo_envio_toggle(request, metodo_id):
    metodo = get_object_or_404(MetodoEnvio, id=metodo_id)

    if request.method == 'POST':
        metodo.activo = not metodo.activo
        metodo.save(update_fields=['activo'])
        estado = 'activo' if metodo.activo else 'inactivo'
        messages.success(request, f'El método "{metodo.nombre}" ahora está {estado}.')

    return redirect('admin_metodos_envio')


@admin_required
def admin_metodo_envio_eliminar(request, metodo_id):
    metodo = get_object_or_404(MetodoEnvio, id=metodo_id)

    if request.method == 'POST':
        try:
            metodo.delete()
            messages.success(request, 'Método de envío eliminado correctamente.')
        except ProtectedError:
            messages.warning(
                request,
                f'No se puede eliminar "{metodo.nombre}" porque ya está asociado a envíos.',
            )

    return redirect('admin_metodos_envio')


@admin_required
def admin_facturacion(request):
    """Vista de facturación con pedidos pagados y finalizados"""
    # Obtener pedidos pagados y entregados
    pedidos = Pedido.objects.filter(
        estado__in=['pagado', 'entregado']
    ).select_related('usuario').prefetch_related('items__producto').order_by('-creado')
    
    # Calcular totales
    total_ingresos = pedidos.aggregate(
        total=Sum('total')
    )['total'] or 0
    
    total_pedidos = pedidos.count()
    
    # Calcular promedio por pedido
    promedio_pedido = total_ingresos / total_pedidos if total_pedidos > 0 else 0
    
    context = {
        'pedidos': pedidos,
        'total_ingresos': total_ingresos,
        'total_pedidos': total_pedidos,
        'promedio_pedido': promedio_pedido,
        'estados_choices': ESTADOS_PEDIDO,
    }
    
    return render(request, 'admin_panel/facturacion.html', context)


@admin_required
def admin_exportar_facturacion_csv(request):
    """Exportar pedidos de facturación a CSV"""
    pedidos = Pedido.objects.filter(
        estado__in=['pagado', 'entregado']
    ).select_related('usuario').prefetch_related('items__producto').order_by('-creado')
    
    response = HttpResponse(content_type='text/csv')
    filename = f"facturacion_{datetime.now().strftime('%Y-%m-%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Encabezados
    writer.writerow([
        'ID Pedido',
        'Fecha', 
        'Cliente',
        'Email',
        'Estado',
        'Método Pago',
        'Subtotal',
        'Costo Envío',
        'Total',
        'Dirección',
        'Ciudad',
        'Teléfono',
        'Productos',
        'Cantidad Items'
    ])
    
    for pedido in pedidos:
        # Lista de productos
        productos = []
        for item in pedido.items.all():
            productos.append(f"{item.producto.nombre} x{item.cantidad}")
        
        writer.writerow([
            pedido.id,
            pedido.creado.strftime('%Y-%m-%d %H:%M'),
            pedido.nombre_completo or pedido.usuario.get_full_name() or pedido.usuario.username,
            pedido.usuario.email,
            pedido.get_estado_display(),
            pedido.get_metodo_pago_display() or 'N/A',
            pedido.subtotal,
            pedido.costo_envio,
            pedido.total,
            pedido.direccion,
            pedido.ciudad,
            pedido.telefono,
            ' | '.join(productos),
            pedido.items.count()
        ])
    
    return response
