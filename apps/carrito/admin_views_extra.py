from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Sum, Count
from .models import Pedido, ItemPedido, PerfilUsuario

def es_admin(user):
    return user.is_staff

@login_required
@user_passes_test(es_admin, login_url='/admin/login/')
def admin_usuarios(request):
    """Ver todos los usuarios registrados (solo admin)"""
    usuarios = User.objects.all().order_by('-date_joined')
    
    # Estadísticas
    usuarios_staff = usuarios.filter(is_staff=True)
    usuarios_clientes = usuarios.filter(is_staff=False)
    usuarios_activos = usuarios.filter(last_login__isnull=False)
    
    context = {
        'usuarios': usuarios,
        'usuarios_staff': usuarios_staff,
        'usuarios_clientes': usuarios_clientes,
        'usuarios_activos': usuarios_activos,
    }
    
    return render(request, 'carrito/admin_usuarios.html', context)

@login_required
@user_passes_test(es_admin, login_url='/admin/login/')
def admin_pedidos_todos(request):
    """Ver todos los pedidos de todos los usuarios (solo admin)"""
    pedidos = Pedido.objects.all().select_related('usuario').prefetch_related('items__producto').order_by('-creado')
    
    context = {
        'pedidos': pedidos,
        'total_pedidos': pedidos.count(),
        'total_ingresos': pedidos.aggregate(total=Sum('total'))['total'] or 0,
    }
    
    return render(request, 'carrito/admin_pedidos_todos.html', context)

@login_required
@user_passes_test(es_admin, login_url='/admin/login/')
def admin_usuario_pedidos(request, user_id):
    """Ver todos los pedidos de un usuario específico (solo admin)"""
    usuario = get_object_or_404(User, id=user_id)
    pedidos = Pedido.objects.filter(usuario=usuario).prefetch_related('items__producto').order_by('-creado')
    
    context = {
        'usuario_objetivo': usuario,
        'pedidos': pedidos,
        'total_pedidos': pedidos.count(),
        'total_gastado': pedidos.aggregate(total=Sum('total'))['total'] or 0,
    }
    
    return render(request, 'carrito/admin_usuario_pedidos.html', context)

@login_required
@user_passes_test(es_admin, login_url='/admin/login/')
def admin_estadisticas(request):
    """Estadísticas detalladas del sistema (solo admin)"""
    from django.db.models import Count
    
    # Estadísticas generales
    total_usuarios = User.objects.count()
    total_pedidos = Pedido.objects.count()
    pedidos_por_estado = Pedido.objects.values('estado').annotate(count=Count('id'))
    
    # Top usuarios por gastos
    top_usuarios = User.objects.annotate(
        total_gastado=Sum('pedido__total')
    ).filter(total_gastado__isnull=False).order_by('-total_gastado')[:10]
    
    context = {
        'total_usuarios': total_usuarios,
        'total_pedidos': total_pedidos,
        'pedidos_por_estado': pedidos_por_estado,
        'top_usuarios': top_usuarios,
    }
    
    return render(request, 'carrito/admin_estadisticas.html', context)
