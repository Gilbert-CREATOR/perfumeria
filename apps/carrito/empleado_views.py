from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count
from django.views.decorators.http import require_POST
from django.views.decorators.debug import sensitive_post_parameters
from django.db import transaction
from .forms import EmpleadoCrearForm, EmpleadoEditarForm
from .models import PerfilUsuario, Pedido

def es_admin_o_empleado(user):
    """Verificar si es admin o empleado"""
    if not user.is_authenticated:
        return False
    try:
        perfil = user.perfil
        return perfil.tipo_usuario in ['admin', 'empleado']
    except PerfilUsuario.DoesNotExist:
        return user.is_staff  # Fallback para usuarios existentes

def es_admin(user):
    """Verificar si es administrador"""
    if not user.is_authenticated:
        return False
    try:
        perfil = user.perfil
        return perfil.tipo_usuario == 'admin'
    except PerfilUsuario.DoesNotExist:
        return user.is_staff  # Fallback para usuarios existentes

@login_required
@sensitive_post_parameters('password')
def agregar_empleado(request):
    """Agregar nuevo empleado (solo admin)"""
    if not es_admin(request.user):
        messages.error(request, 'No tienes permiso para agregar empleados')
        return redirect('admin_usuarios')
    
    if request.method == 'POST':
        form = EmpleadoCrearForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                nuevo_usuario = form.save()
            messages.success(request, f'Empleado {nuevo_usuario.username} agregado correctamente')
            return redirect('admin_usuarios')
        for errores in form.errors.values():
            for error in errores:
                messages.error(request, error)
    
    return render(request, 'carrito/agregar_empleado.html')

@login_required
@user_passes_test(es_admin_o_empleado, login_url='/admin/login/')
def panel_empleado(request):
    """Panel principal para empleados"""
    try:
        perfil = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        # Crear perfil si no existe
        perfil = PerfilUsuario.objects.create(
            usuario=request.user,
            tipo_usuario='admin' if request.user.is_staff else 'cliente'
        )
    
    # Estadísticas
    total_usuarios = User.objects.count()
    total_pedidos = Pedido.objects.count()
    pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
    
    context = {
        'perfil': perfil,
        'total_usuarios': total_usuarios,
        'total_pedidos': total_pedidos,
        'pedidos_pendientes': pedidos_pendientes,
    }
    
    return render(request, 'carrito/panel_empleado.html', context)

@login_required
@user_passes_test(es_admin_o_empleado, login_url='/admin/login/')
def empleados_lista(request):
    """Ver lista de empleados (admin y empleados)"""
    try:
        perfil_actual = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'No tienes perfil configurado')
        return redirect('panel_empleado')
    
    # Obtener empleados
    empleados_perfil = PerfilUsuario.objects.filter(tipo_usuario='empleado').select_related('usuario')
    
    # También incluir admins si es admin
    if perfil_actual.es_admin:
        admins_perfil = PerfilUsuario.objects.filter(tipo_usuario='admin').select_related('usuario')
        empleados_perfil = empleados_perfil | admins_perfil
    
    context = {
        'empleados': empleados_perfil,
        'perfil_actual': perfil_actual,
        'es_admin': perfil_actual.es_admin,
    }
    
    return render(request, 'carrito/empleados_lista.html', context)

@login_required
@user_passes_test(es_admin, login_url='/admin/login/')
def editar_empleado(request, user_id):
    """Editar empleado (solo admin)"""
    if not es_admin(request.user):
        messages.error(request, 'No tienes permiso para editar empleados')
        return redirect('empleados_lista')
    
    empleado = get_object_or_404(PerfilUsuario, usuario_id=user_id)
    
    if request.method == 'POST':
        usuario = empleado.usuario
        form = EmpleadoEditarForm(request.POST, usuario=usuario)
        if form.is_valid():
            with transaction.atomic():
                usuario.first_name = form.cleaned_data['first_name']
                usuario.last_name = form.cleaned_data['last_name']
                usuario.email = form.cleaned_data['email']
                usuario.save(update_fields=['first_name', 'last_name', 'email'])
                empleado.telefono = form.cleaned_data['telefono']
                empleado.direccion = form.cleaned_data['direccion']
                empleado.tipo_usuario = form.cleaned_data['tipo_usuario']
                empleado.save(update_fields=['telefono', 'direccion', 'tipo_usuario', 'actualizado'])
            messages.success(request, f'Empleado {usuario.username} actualizado correctamente')
            return redirect('empleados_lista')
        for errores in form.errors.values():
            for error in errores:
                messages.error(request, error)
    
    context = {
        'empleado': empleado,
    }
    
    return render(request, 'carrito/editar_empleado.html', context)

@login_required
@user_passes_test(es_admin, login_url='/admin/login/')
@require_POST
def eliminar_empleado(request, user_id):
    """Eliminar empleado (solo admin)"""
    if not es_admin(request.user):
        messages.error(request, 'No tienes permiso para eliminar empleados')
        return redirect('empleados_lista')
    
    empleado = get_object_or_404(PerfilUsuario, usuario_id=user_id)
    
    # No permitir eliminarse a sí mismo
    if empleado.usuario == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta')
        return redirect('empleados_lista')
    
    nombre_usuario = empleado.usuario.username
    empleado.usuario.delete()
    
    messages.success(request, f'Empleado {nombre_usuario} eliminado correctamente')
    return redirect('empleados_lista')
