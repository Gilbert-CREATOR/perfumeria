from functools import wraps
import csv
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import DecimalField, F, Q, Sum
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.debug import sensitive_post_parameters

from apps.productos.forms import ResenaForm
from apps.productos.models import Producto, Resena
from apps.core.forms import ArticuloBlogForm, ConfiguracionSitioForm, DisenoCorreoForm, MensajeContactoAdminForm, PreguntaFrecuenteForm
from apps.core.models import ArticuloBlog, ConfiguracionSitio, DisenoCorreo, MensajeContacto, PreguntaFrecuente, RegistroAuditoria
from apps.newsletter.models import SuscriptorNewsletter
from .admin_forms import EnvioForm, MetodoEnvioForm, PedidoAdminForm, ProductoAdminForm, UsuarioPanelForm
from .emails import (
    enviar_email_cancelacion_reembolso,
    enviar_email_envio_despachado,
    enviar_email_pedido_entregado,
    enviar_email_pedido_preparacion,
    enviar_email_recomendaciones,
    enviar_email_solicitud_resena,
)
from .models import ESTADOS_PEDIDO, Envio, ItemPedido, MetodoEnvio, MovimientoInventario, Pedido
from .services import reintegrar_stock_pedido

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


def puede_gestionar_usuario(actor, objetivo):
    return actor.is_superuser or not objetivo.is_superuser


def parse_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {'1', 'true', 'on', 'yes', 'si'}


def count_by_choices(queryset, field_name, choices):
    return {
        key: queryset.filter(**{field_name: key}).count()
        for key, _label in choices
    }


def notificar_cambio_envio(envio, estado_anterior=None):
    """Envía una sola notificación cuando el envío alcanza un hito nuevo."""
    if not envio.pedido.usuario or not envio.pedido.usuario.email:
        return
    if envio.estado == 'entregado' and estado_anterior != 'entregado':
        enviar_email_pedido_entregado(envio.pedido)
        enviar_email_recomendaciones(envio.pedido)
        enviar_email_solicitud_resena(envio.pedido)
    elif envio.estado == 'preparando' and estado_anterior != 'preparando':
        enviar_email_pedido_preparacion(envio.pedido)
    elif (
        envio.estado in {'despachado', 'en_transito'}
        and estado_anterior not in {'despachado', 'en_transito', 'entregado'}
    ):
        enviar_email_envio_despachado(envio.pedido)


@admin_required
def admin_auditoria(request):
    registros = RegistroAuditoria.objects.select_related('usuario')[:500]
    return render(request, 'admin_panel/auditoria.html', {'registros': registros})


@admin_required
def admin_diagnostico(request):
    resultado_email = None
    if request.method == 'POST' and request.POST.get('accion') == 'probar_email':
        destino = request.POST.get('email', '').strip() or request.user.email
        if not destino:
            messages.error(request, 'Indica un correo para la prueba.')
        else:
            try:
                enviados = send_mail(
                    'D.A.R.C.Y. — Prueba de correo',
                    'La configuración de correo está funcionando correctamente.',
                    settings.DEFAULT_FROM_EMAIL,
                    [destino],
                    fail_silently=False,
                )
                resultado_email = bool(enviados)
                messages.success(request, f'Correo de prueba enviado a {destino}.')
            except Exception as error:
                resultado_email = False
                messages.error(request, f'No se pudo enviar: {error}')

    contexto = {
        'resultado_email': resultado_email,
        'email_backend': settings.EMAIL_BACKEND,
        'email_remitente': settings.DEFAULT_FROM_EMAIL,
        'resend_configurado': bool(getattr(settings, 'RESEND_API_KEY', '')),
        'paypal_configurado': bool(
            getattr(settings, 'PAYPAL_CLIENT_ID', '')
            and getattr(settings, 'PAYPAL_SECRET', '')
            and getattr(settings, 'PAYPAL_WEBHOOK_ID', '')
        ),
    }
    return render(request, 'admin_panel/diagnostico.html', contexto)


@admin_required
def admin_blog(request):
    return render(request, 'admin_panel/blog.html', {'articulos': ArticuloBlog.objects.select_related('autor')})


@admin_required
def admin_blog_form(request, articulo_id=None):
    articulo = get_object_or_404(ArticuloBlog, pk=articulo_id) if articulo_id else None
    form = ArticuloBlogForm(request.POST or None, instance=articulo)
    if request.method == 'POST' and form.is_valid():
        articulo = form.save(commit=False)
        articulo.autor = articulo.autor or request.user
        articulo.save()
        messages.success(request, 'Artículo guardado correctamente.')
        return redirect('admin_blog')
    return render(request, 'admin_panel/blog_form.html', {'form': form, 'articulo': articulo})


@admin_required
def admin_blog_eliminar(request, articulo_id):
    articulo = get_object_or_404(ArticuloBlog, pk=articulo_id)
    if request.method == 'POST':
        articulo.delete()
        messages.success(request, 'Artículo eliminado.')
    return redirect('admin_blog')


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
        'usuarios': User.objects.count(),
        'suscriptores': SuscriptorNewsletter.objects.filter(activo=True).count(),
        'mensajes_nuevos': MensajeContacto.objects.filter(estado='nuevo').count(),
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
def admin_usuarios(request):
    usuarios = User.objects.all().order_by('-date_joined')
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    if q:
        usuarios = usuarios.filter(
            Q(username__icontains=q) | Q(email__icontains=q)
            | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    if estado == 'activos':
        usuarios = usuarios.filter(is_active=True)
    elif estado == 'inactivos':
        usuarios = usuarios.filter(is_active=False)
    elif estado == 'staff':
        usuarios = usuarios.filter(is_staff=True)
    elif estado == 'clientes':
        usuarios = usuarios.filter(is_staff=False)
    return render(request, 'admin_panel/usuarios.html', {
        'usuarios': usuarios,
        'busqueda': q,
        'estado_actual': estado,
        'total_usuarios': User.objects.count(),
        'usuarios_activos': User.objects.filter(is_active=True).count(),
        'usuarios_staff': User.objects.filter(is_staff=True).count(),
    })


@sensitive_post_parameters('nueva_contrasena')
@admin_required
def admin_usuario_crear(request):
    form = UsuarioPanelForm(request.POST or None, actor=request.user)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        messages.success(request, f'Cuenta de {usuario.username} creada correctamente.')
        return redirect('admin_usuarios')
    return render(request, 'admin_panel/usuario_form.html', {
        'form': form, 'usuario_objetivo': None, 'titulo': 'Nuevo usuario',
    })


@sensitive_post_parameters('nueva_contrasena')
@admin_required
def admin_usuario_editar(request, usuario_id):
    usuario = get_object_or_404(User, pk=usuario_id)
    if not puede_gestionar_usuario(request.user, usuario):
        messages.error(request, 'Solo otro superusuario puede modificar esa cuenta.')
        return redirect('admin_usuarios')
    form = UsuarioPanelForm(request.POST or None, instance=usuario, actor=request.user)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        messages.success(request, f'Cuenta de {usuario.username} actualizada.')
        return redirect('admin_usuarios')
    return render(request, 'admin_panel/usuario_form.html', {
        'form': form, 'usuario_objetivo': usuario, 'titulo': f'Editar {usuario.username}',
    })


@admin_required
def admin_usuario_toggle(request, usuario_id):
    usuario = get_object_or_404(User, pk=usuario_id)
    if request.method == 'POST':
        if usuario.pk == request.user.pk:
            messages.error(request, 'No puedes desactivar tu propia cuenta.')
        elif not puede_gestionar_usuario(request.user, usuario):
            messages.error(request, 'Solo otro superusuario puede modificar esa cuenta.')
        else:
            usuario.is_active = not usuario.is_active
            usuario.save(update_fields=['is_active'])
            messages.success(request, f'{usuario.username} ahora está {"activo" if usuario.is_active else "inactivo"}.')
    return redirect('admin_usuarios')


@admin_required
def admin_newsletter(request):
    suscriptores = SuscriptorNewsletter.objects.select_related('usuario').all()
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    if q:
        suscriptores = suscriptores.filter(email__icontains=q)
    if estado == 'activos':
        suscriptores = suscriptores.filter(activo=True)
    elif estado == 'inactivos':
        suscriptores = suscriptores.filter(activo=False)
    return render(request, 'admin_panel/newsletter.html', {
        'suscriptores': suscriptores, 'busqueda': q, 'estado_actual': estado,
        'total_suscriptores': SuscriptorNewsletter.objects.count(),
        'suscriptores_activos': SuscriptorNewsletter.objects.filter(activo=True).count(),
    })


@admin_required
def admin_newsletter_toggle(request, suscriptor_id):
    suscriptor = get_object_or_404(SuscriptorNewsletter, pk=suscriptor_id)
    if request.method == 'POST':
        suscriptor.activo = not suscriptor.activo
        suscriptor.save(update_fields=['activo', 'fecha_actualizacion'])
        messages.success(request, f'{suscriptor.email} ahora está {"activo" if suscriptor.activo else "inactivo"}.')
    return redirect('admin_newsletter')


@admin_required
def admin_newsletter_eliminar(request, suscriptor_id):
    suscriptor = get_object_or_404(SuscriptorNewsletter, pk=suscriptor_id)
    if request.method == 'POST':
        email = suscriptor.email
        suscriptor.delete()
        messages.success(request, f'Suscripción de {email} eliminada.')
    return redirect('admin_newsletter')


@admin_required
def admin_newsletter_exportar(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="suscriptores.csv"'
    writer = csv.writer(response)
    writer.writerow(['Correo', 'Activo', 'Usuario', 'Fecha de suscripción'])
    for item in SuscriptorNewsletter.objects.select_related('usuario').all():
        writer.writerow([item.email, 'Sí' if item.activo else 'No', item.usuario.username if item.usuario else '', item.fecha_suscripcion.isoformat()])
    return response


@admin_required
def admin_configuracion(request):
    configuracion = ConfiguracionSitio.cargar()
    form = ConfiguracionSitioForm(request.POST or None, instance=configuracion)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Configuración pública actualizada.')
        return redirect('admin_configuracion')
    return render(request, 'admin_panel/configuracion.html', {'form': form, 'configuracion': configuracion})


PLANTILLAS_CORREO = (
    {'id': 'confirmacion', 'nombre': 'Pedido confirmado', 'etiqueta': 'PEDIDO #1042', 'titulo': 'TU PEDIDO ESTÁ CONFIRMADO.', 'texto': 'Recibimos tu selección y comenzaremos a prepararla.', 'icono': 'fa-bag-shopping'},
    {'id': 'pago', 'nombre': 'Pago confirmado', 'etiqueta': 'PAGO APROBADO', 'titulo': 'TODO LISTO PARA CONTINUAR.', 'texto': 'El pago fue confirmado y tu pedido pasa a preparación.', 'icono': 'fa-credit-card'},
    {'id': 'preparacion', 'nombre': 'Pedido en preparación', 'etiqueta': 'EN PREPARACIÓN', 'titulo': 'TU SELECCIÓN ESTÁ EN PROCESO.', 'texto': 'Estamos preparando cada producto antes del despacho.', 'icono': 'fa-box-open'},
    {'id': 'envio', 'nombre': 'Pedido enviado', 'etiqueta': 'EN CAMINO', 'titulo': 'TU PEDIDO YA SALIÓ.', 'texto': 'Consulta el seguimiento y la fecha estimada de entrega.', 'icono': 'fa-truck-fast'},
    {'id': 'entregado', 'nombre': 'Pedido entregado', 'etiqueta': 'ENTREGA COMPLETADA', 'titulo': 'DISFRUTA TU NUEVA FRAGANCIA.', 'texto': 'Esperamos que cada aroma sea exactamente lo que buscabas.', 'icono': 'fa-circle-check'},
    {'id': 'rechazado', 'nombre': 'Pago rechazado', 'etiqueta': 'ACCIÓN REQUERIDA', 'titulo': 'NO PUDIMOS PROCESAR EL PAGO.', 'texto': 'Puedes volver e intentarlo con otro método de pago.', 'icono': 'fa-circle-exclamation'},
    {'id': 'cancelado', 'nombre': 'Cancelación y reembolso', 'etiqueta': 'PEDIDO CANCELADO', 'titulo': 'TU REEMBOLSO ESTÁ EN PROCESO.', 'texto': 'Te informaremos cuando la devolución haya sido completada.', 'icono': 'fa-rotate-left'},
    {'id': 'bienvenida', 'nombre': 'Bienvenida y verificación', 'etiqueta': 'BIENVENIDO A D.A.R.C.Y.', 'titulo': 'TU EXPERIENCIA COMIENZA AQUÍ.', 'texto': 'Verifica tu dirección de correo para activar tu cuenta.', 'icono': 'fa-user-check'},
    {'id': 'password', 'nombre': 'Recuperar contraseña', 'etiqueta': 'SEGURIDAD DE CUENTA', 'titulo': 'RESTABLECE TU CONTRASEÑA.', 'texto': 'Usa el enlace seguro para volver a entrar a tu cuenta.', 'icono': 'fa-key'},
    {'id': 'disponible', 'nombre': 'Producto disponible', 'etiqueta': 'NUEVAMENTE DISPONIBLE', 'titulo': 'VOLVIÓ UNO DE TUS FAVORITOS.', 'texto': 'El perfume que estabas esperando ya tiene existencias.', 'icono': 'fa-spray-can-sparkles'},
    {'id': 'recomendaciones', 'nombre': 'Recomendaciones', 'etiqueta': 'CURADO PARA TI', 'titulo': 'AROMAS QUE PUEDEN GUSTARTE.', 'texto': 'Una selección basada en tu historial y temporadas favoritas.', 'icono': 'fa-wand-magic-sparkles'},
    {'id': 'resena', 'nombre': 'Solicitud de reseña', 'etiqueta': 'TU OPINIÓN IMPORTA', 'titulo': 'CUÉNTANOS TU EXPERIENCIA.', 'texto': 'Comparte una reseña del perfume que recibiste.', 'icono': 'fa-star'},
    {'id': 'carrito', 'nombre': 'Carrito abandonado', 'etiqueta': 'GUARDAMOS TU SELECCIÓN', 'titulo': 'TODAVÍA ESTÁN EN TU CARRITO.', 'texto': 'Vuelve cuando estés listo para completar la compra.', 'icono': 'fa-cart-shopping'},
    {'id': 'newsletter', 'nombre': 'Newsletter', 'etiqueta': 'D.A.R.C.Y. JOURNAL', 'titulo': 'NUEVAS HISTORIAS EN PERFUMERÍA.', 'texto': 'Lanzamientos, selecciones y novedades de la tienda.', 'icono': 'fa-envelope-open-text'},
)


@admin_required
def admin_correos(request):
    diseno = DisenoCorreo.cargar()
    form = DisenoCorreoForm(request.POST or None, instance=diseno)
    accion = request.POST.get('accion') if request.method == 'POST' else ''

    if request.method == 'POST' and accion in {'guardar', 'enviar_prueba'} and form.is_valid():
        diseno = form.save()
        if accion == 'guardar':
            messages.success(request, 'Diseño de correos actualizado. Los próximos envíos usarán estos cambios.')
            return redirect('admin_correos')

        destino = request.POST.get('email_prueba', '').strip() or request.user.email
        if not destino:
            messages.error(request, 'Indica un correo para enviar la prueba.')
        else:
            contexto = {
                'pedido_id': '#PREVIEW-1042',
                'cliente_nombre': request.user.get_full_name() or request.user.username,
                'total': 7500,
                'productos': ['Invictus', 'Versace Eros'],
                'site_url': getattr(settings, 'PUBLIC_SITE_URL', 'http://127.0.0.1:8000').rstrip('/'),
                'catalogo_url': f"{getattr(settings, 'PUBLIC_SITE_URL', 'http://127.0.0.1:8000').rstrip('/')}/catalogo/",
            }
            try:
                html = render_to_string('emails/pedido_confirmado_test.html', contexto)
                send_mail(
                    subject='D.A.R.C.Y. — Vista previa del diseño de correo',
                    message=strip_tags(html),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[destino],
                    html_message=html,
                    fail_silently=False,
                )
                messages.success(request, f'Vista previa enviada a {destino}.')
            except Exception as error:
                messages.error(request, f'El diseño se guardó, pero la prueba no pudo enviarse: {error}')
        return redirect('admin_correos')

    return render(request, 'admin_panel/correos.html', {
        'form': form,
        'diseno': diseno,
        'plantillas': PLANTILLAS_CORREO,
    })


@admin_required
def admin_faq(request):
    return render(request, 'admin_panel/faq.html', {'preguntas': PreguntaFrecuente.objects.all()})


@admin_required
def admin_faq_crear(request):
    form = PreguntaFrecuenteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Pregunta frecuente creada.')
        return redirect('admin_faq')
    return render(request, 'admin_panel/faq_form.html', {'form': form, 'titulo': 'Nueva pregunta'})


@admin_required
def admin_faq_editar(request, pregunta_id):
    pregunta = get_object_or_404(PreguntaFrecuente, pk=pregunta_id)
    form = PreguntaFrecuenteForm(request.POST or None, instance=pregunta)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Pregunta frecuente actualizada.')
        return redirect('admin_faq')
    return render(request, 'admin_panel/faq_form.html', {'form': form, 'titulo': 'Editar pregunta'})


@admin_required
def admin_faq_eliminar(request, pregunta_id):
    pregunta = get_object_or_404(PreguntaFrecuente, pk=pregunta_id)
    if request.method == 'POST':
        pregunta.delete()
        messages.success(request, 'Pregunta frecuente eliminada.')
    return redirect('admin_faq')


@admin_required
def admin_mensajes(request):
    mensajes_qs = MensajeContacto.objects.all()
    estado = request.GET.get('estado', '').strip()
    q = request.GET.get('q', '').strip()
    if estado:
        mensajes_qs = mensajes_qs.filter(estado=estado)
    if q:
        mensajes_qs = mensajes_qs.filter(Q(nombre__icontains=q) | Q(email__icontains=q) | Q(asunto__icontains=q))
    return render(request, 'admin_panel/mensajes.html', {
        'mensajes_contacto': mensajes_qs, 'estado_actual': estado, 'busqueda': q,
        'mensajes_nuevos': MensajeContacto.objects.filter(estado='nuevo').count(),
        'estados_mensaje': MensajeContacto.ESTADOS,
    })


@admin_required
def admin_mensaje_detalle(request, mensaje_id):
    mensaje = get_object_or_404(MensajeContacto, pk=mensaje_id)
    form = MensajeContactoAdminForm(request.POST or None, instance=mensaje)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Mensaje actualizado.')
        return redirect('admin_mensaje_detalle', mensaje_id=mensaje.id)
    return render(request, 'admin_panel/mensaje_detalle.html', {'mensaje_contacto': mensaje, 'form': form})


@admin_required
def admin_mensaje_eliminar(request, mensaje_id):
    mensaje = get_object_or_404(MensajeContacto, pk=mensaje_id)
    if request.method == 'POST':
        mensaje.delete()
        messages.success(request, 'Mensaje eliminado.')
    return redirect('admin_mensajes')


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
def admin_resenas(request):
    resenas = Resena.objects.select_related('usuario', 'producto').order_by('-creado', '-id')
    q = request.GET.get('q', '').strip()
    estrellas = request.GET.get('estrellas', '').strip()

    if q:
        resenas = resenas.filter(
            Q(usuario__username__icontains=q)
            | Q(usuario__email__icontains=q)
            | Q(producto__nombre__icontains=q)
            | Q(comentario__icontains=q)
        )
    if estrellas in {'1', '2', '3', '4', '5'}:
        resenas = resenas.filter(estrellas=int(estrellas))

    return render(
        request,
        'admin_panel/resenas.html',
        {
            'resenas': resenas,
            'busqueda': q,
            'estrellas_actuales': estrellas,
            'total_resenas': resenas.count(),
        },
    )


@admin_required
def admin_resena_editar(request, resena_id):
    resena = get_object_or_404(Resena.objects.select_related('usuario', 'producto'), pk=resena_id)
    form = ResenaForm(request.POST or None, instance=resena)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Reseña actualizada correctamente.')
        return redirect('admin_resenas')

    return render(
        request,
        'admin_panel/resena_form.html',
        {'form': form, 'resena': resena},
    )


@admin_required
def admin_resena_eliminar(request, resena_id):
    resena = get_object_or_404(Resena, pk=resena_id)
    if request.method == 'POST':
        resena.delete()
        messages.success(request, 'Reseña eliminada correctamente.')
    return redirect('admin_resenas')


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
            estado_anterior = pedido.estado
            pedido_form = PedidoAdminForm(request.POST, instance=pedido)
            if pedido_form.is_valid():
                pedido_actualizado = pedido_form.save()
                if pedido_actualizado.estado == 'cancelado' and estado_anterior != 'cancelado':
                    reintegrar_stock_pedido(pedido_actualizado)
                    enviar_email_cancelacion_reembolso(pedido_actualizado)
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

                notificar_cambio_envio(nuevo_envio)
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
                    with transaction.atomic():
                        producto = Producto.objects.select_for_update().get(pk=producto.pk)
                        stock_anterior = producto.stock
                        producto.stock = nuevo_stock
                        if 'disponible' in request.POST:
                            producto.disponible = parse_bool(request.POST.get('disponible'))
                        producto.save()
                        if stock_anterior != nuevo_stock:
                            MovimientoInventario.objects.create(
                                producto=producto,
                                producto_nombre=producto.nombre,
                                usuario=request.user,
                                tipo='ajuste',
                                cantidad=nuevo_stock - stock_anterior,
                                stock_anterior=stock_anterior,
                                stock_resultante=nuevo_stock,
                                motivo=(request.POST.get('motivo') or 'Ajuste manual desde el panel')[:240],
                            )
                    messages.success(request, f'Stock de "{producto.nombre}" actualizado.')

        elif accion == 'toggle_disponibilidad':
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
def admin_movimientos_inventario(request):
    movimientos = MovimientoInventario.objects.select_related(
        'producto', 'pedido', 'usuario',
    )[:500]
    return render(
        request,
        'admin_panel/movimientos_inventario.html',
        {'movimientos': movimientos},
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
    estado_anterior = envio.estado
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

            notificar_cambio_envio(envio, estado_anterior)
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
