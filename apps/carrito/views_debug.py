from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .models import Pedido

def es_admin(user):
    return user.is_staff

@login_required
@user_passes_test(es_admin, login_url='/admin/login/')
def debug_pedidos(request):
    # Obtener todos los usuarios y pedidos
    usuarios = User.objects.all()
    todos_los_pedidos = Pedido.objects.all().order_by('-creado')
    pedidos_usuario = Pedido.objects.filter(usuario=request.user).order_by('-creado')
    
    context = {
        'usuarios': usuarios,
        'todos_los_pedidos': todos_los_pedidos,
        'pedidos_usuario': pedidos_usuario,
        'usuario_actual': request.user,
    }
    
    return render(request, 'carrito/debug_pedidos.html', context)
