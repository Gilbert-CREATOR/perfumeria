from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from apps.carrito.models import Pedido
from apps.productos.models import Favorito
from .models import PerfilUsuario, Direccion
from .forms import PerfilForm, DireccionForm
from django.contrib import messages


def login_usuario(request):
    if request.user.is_authenticated:
        return redirect('/')
        
    if request.method == 'POST':
        # Permitir login con email o username
        login_field = request.POST['username']
        password = request.POST['password']

        # Si el login_field contiene @, es un email
        if '@' in login_field:
            try:
                user_obj = User.objects.get(email=login_field)
                username = user_obj.username
            except User.DoesNotExist:
                user = None
                username = None
        else:
            username = login_field

        if username:
            user = authenticate(request, username=username, password=password)
        else:
            user = None

        if user:
            login(request, user)
            # Si el usuario es admin, redirigir al panel de administración
            if user.is_staff or user.is_superuser:
                next_url = '/admin/panel/'
            else:
                next_url = request.GET.get('next', '/')
            messages.success(request, f'¡Bienvenido {user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'usuarios/login.html')


def logout_usuario(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente')
    return redirect('/')


def registro_usuario(request):
    if request.user.is_authenticated:
        return redirect('/')
        
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        password_confirm = request.POST['password_confirm']
        email = request.POST.get('email', '')
        
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'usuarios/register.html')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe')
            return render(request, 'usuarios/register.html')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'¡Cuenta creada! Bienvenido {user.username}')
            return redirect('/')

    return render(request, 'usuarios/register.html')


@login_required
def mi_cuenta(request):
    """Vista del perfil de usuario con estadísticas"""
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-creado')
    favoritos = Favorito.objects.filter(usuario=request.user).select_related('producto')
    
    # Calcular estadísticas
    total_pedidos = pedidos.count()
    total_gastado = sum(pedido.total for pedido in pedidos if pedido.total)
    total_favoritos = favoritos.count()
    
    context = {
        'pedidos': pedidos[:5],  # Últimos 5 pedidos
        'total_pedidos': total_pedidos,
        'total_gastado': total_gastado,
        'total_favoritos': total_favoritos,
        'favoritos': favoritos[:6],  # Últimos 6 favoritos
    }
    return render(request, 'usuarios/mi_cuenta.html', context)


@login_required
def perfil(request):
    perfil, created = PerfilUsuario.objects.get_or_create(usuario=request.user)
    direcciones = Direccion.objects.filter(usuario=request.user)
    
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=perfil)
    
    return render(request, 'usuarios/perfil.html', {
        'form': form,
        'direcciones': direcciones
    })


@login_required
def agregar_direccion(request):
    if request.method == 'POST':
        form = DireccionForm(request.POST)
        if form.is_valid():
            direccion = form.save(commit=False)
            direccion.usuario = request.user
            direccion.save()
            messages.success(request, 'Dirección agregada correctamente')
            return redirect('perfil')
    else:
        form = DireccionForm()
    
    return render(request, 'usuarios/agregar_direccion.html', {
        'form': form
    })


@login_required
def editar_direccion(request, direccion_id):
    direccion = get_object_or_404(Direccion, id=direccion_id, usuario=request.user)
    
    if request.method == 'POST':
        form = DireccionForm(request.POST, instance=direccion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dirección actualizada correctamente')
            return redirect('perfil')
    else:
        form = DireccionForm(instance=direccion)
    
    return render(request, 'usuarios/editar_direccion.html', {
        'form': form,
        'direccion': direccion
    })


@login_required
def eliminar_direccion(request, direccion_id):
    direccion = get_object_or_404(Direccion, id=direccion_id, usuario=request.user)
    
    if request.method == 'POST':
        direccion.delete()
        messages.success(request, 'Dirección eliminada correctamente')
        return redirect('perfil')
    
    return render(request, 'usuarios/eliminar_direccion.html', {
        'direccion': direccion
    })


@login_required
def establecer_predeterminada(request, direccion_id):
    direccion = get_object_or_404(Direccion, id=direccion_id, usuario=request.user)
    direccion.es_predeterminada = True
    direccion.save()
    
    messages.success(request, f'Dirección {direccion.direccion} establecida como predeterminada')
    return redirect('perfil')
