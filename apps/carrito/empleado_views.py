from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count
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
def agregar_empleado(request):
    """Agregar nuevo empleado (solo admin)"""
    if not es_admin(request.user):
        messages.error(request, 'No tienes permiso para agregar empleados')
        return redirect('admin_usuarios')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        
        # Validaciones
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe')
            return redirect('agregar_empleado')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado')
            return redirect('agregar_empleado')
        
        try:
            # Crear usuario
            nuevo_usuario = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Crear perfil de empleado
            PerfilUsuario.objects.create(
                usuario=nuevo_usuario,
                tipo_usuario='empleado',
                telefono=telefono,
                direccion=direccion
            )
            
            messages.success(request, f'Empleado {username} agregado correctamente')
            return redirect('admin_usuarios')
            
        except Exception as e:
            messages.error(request, f'Error al agregar empleado: {str(e)}')
            return redirect('agregar_empleado')
    
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
        # Actualizar datos del usuario
        usuario = empleado.usuario
        usuario.first_name = request.POST.get('first_name')
        usuario.last_name = request.POST.get('last_name')
        usuario.email = request.POST.get('email')
        usuario.save()
        
        # Actualizar perfil
        empleado.telefono = request.POST.get('telefono')
        empleado.direccion = request.POST.get('direccion')
        
        # Cambiar rol (solo admin puede cambiar roles)
        nuevo_rol = request.POST.get('tipo_usuario')
        if nuevo_rol in ['admin', 'empleado', 'cliente']:
            empleado.tipo_usuario = nuevo_rol
        
        empleado.save()
        
        messages.success(request, f'Empleado {usuario.username} actualizado correctamente')
        return redirect('empleados_lista')
    
    context = {
        'empleado': empleado,
    }
    
    return render(request, 'carrito/editar_empleado.html', context)

@login_required
@user_passes_test(es_admin, login_url='/admin/login/')
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
