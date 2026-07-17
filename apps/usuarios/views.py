from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from apps.carrito.models import Pedido
from apps.productos.models import Favorito
from .models import PerfilUsuario, Direccion
from .forms import PerfilForm, DireccionForm
from django.contrib import messages
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.core import signing
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.http import require_POST
import hashlib

from apps.carrito.services import complete_pending_cart_item
from .emails import VERIFICACION_SALT, enviar_email_bienvenida, enviar_email_cuenta_eliminada


FRASE_ELIMINAR_CUENTA = 'ELIMINAR MI CUENTA'


def finish_pending_cart(request):
    result = complete_pending_cart_item(request)
    if result is None:
        return False

    success, message = result
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    return True


def safe_next_url(request, default='/'):
    next_url = request.GET.get('next') or default
    if url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return default


def login_usuario(request):
    if request.user.is_authenticated:
        return redirect('/')
        
    if request.method == 'POST':
        # Resuelve ambas credenciales sin depender de que el valor contenga "@".
        login_field = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remote = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[0].strip()
        attempt_key = 'login-attempt:' + hashlib.sha256(f'{remote}:{login_field.lower()}'.encode()).hexdigest()
        intentos = cache.get(attempt_key, 0)
        if intentos >= 5:
            messages.error(request, 'Demasiados intentos. Espera 15 minutos antes de volver a intentarlo.')
            return render(request, 'usuarios/login.html', status=429)

        user_obj = User.objects.filter(username__iexact=login_field).order_by('id').first()
        if user_obj is None:
            user_obj = User.objects.filter(email__iexact=login_field).order_by('id').first()
        username = user_obj.username if user_obj else None

        if username:
            user = authenticate(request, username=username, password=password)
        else:
            user = None

        if user:
            cache.delete(attempt_key)
            login(request, user)
            has_pending_cart = finish_pending_cart(request)
            # Si el usuario es admin, redirigir al panel de administración
            if has_pending_cart:
                next_url = reverse('ver_carrito')
            elif user.is_staff or user.is_superuser:
                next_url = '/admin/panel/'
            else:
                next_url = safe_next_url(request)
            messages.success(request, f'¡Bienvenido {user.username}!')
            return redirect(next_url)
        else:
            cache.set(attempt_key, intentos + 1, timeout=15 * 60)
            messages.error(request, 'Usuario, correo o contraseña incorrectos')

    return render(request, 'usuarios/login.html')


@require_POST
def logout_usuario(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente')
    return redirect('/')


def registro_usuario(request):
    if request.user.is_authenticated:
        return redirect('/')
        
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password1', '')
        password_confirm = request.POST.get('password2', '')
        email = request.POST.get('email', '').strip().lower()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        if not username:
            messages.error(request, 'El nombre de usuario es obligatorio.')
            return render(request, 'usuarios/register.html')
        
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'usuarios/register.html')

        if not email:
            messages.error(request, 'El correo electrónico es obligatorio.')
            return render(request, 'usuarios/register.html')

        candidato = User(username=username, email=email, first_name=first_name, last_name=last_name)
        try:
            validate_password(password, user=candidato)
        except ValidationError as exc:
            for error in exc.messages:
                messages.error(request, error)
            return render(request, 'usuarios/register.html')
            
        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'El usuario ya existe')
            return render(request, 'usuarios/register.html')

        if email and User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Ya existe una cuenta con ese correo electrónico')
            return render(request, 'usuarios/register.html')
        
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
        except IntegrityError:
            messages.error(request, 'Ese usuario o correo ya está registrado.')
            return render(request, 'usuarios/register.html')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            enviar_email_bienvenida(user)
            has_pending_cart = finish_pending_cart(request)
            messages.success(request, f'¡Cuenta creada! Bienvenido {user.username}')
            if has_pending_cart:
                return redirect('ver_carrito')
            return redirect(safe_next_url(request))

    return render(request, 'usuarios/register.html')


def verificar_email(request, token):
    try:
        data = signing.loads(token, salt=VERIFICACION_SALT, max_age=60 * 60 * 24 * 7)
        user = User.objects.get(pk=data['uid'], email=data['email'])
    except (signing.BadSignature, signing.SignatureExpired, KeyError, User.DoesNotExist):
        messages.error(request, 'El enlace de verificación no es válido o ya venció.')
        return redirect('login')

    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=user)
    if not perfil.email_verificado:
        perfil.email_verificado = True
        perfil.save(update_fields=['email_verificado'])
    messages.success(request, 'Tu correo quedó verificado correctamente.')
    return redirect('mi_cuenta' if request.user == user else 'login')


class DarcyPasswordResetView(auth_views.PasswordResetView):
    template_name = 'usuarios/password_reset.html'
    email_template_name = 'emails/password_reset.txt'
    html_email_template_name = 'emails/password_reset.html'
    subject_template_name = 'emails/password_reset_subject.txt'

    def dispatch(self, request, *args, **kwargs):
        site_url = getattr(settings, 'PUBLIC_SITE_URL', 'http://localhost:8000').rstrip('/')
        self.extra_email_context = {
            'site_url': site_url,
            'catalogo_url': f'{site_url}{reverse("catalogo")}',
        }
        return super().dispatch(request, *args, **kwargs)


@login_required
def eliminar_cuenta(request):
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Las cuentas administrativas no se eliminan desde esta opción.')
        return redirect('perfil')

    if request.method == 'POST':
        username_confirmacion = request.POST.get('username_confirmacion', '').strip()
        frase_confirmacion = request.POST.get('frase_confirmacion', '').strip()

        if username_confirmacion != request.user.username:
            messages.error(request, 'El nombre de usuario no coincide.')
        elif frase_confirmacion != FRASE_ELIMINAR_CUENTA:
            messages.error(request, f'Escribe exactamente: {FRASE_ELIMINAR_CUENTA}')
        elif not request.user.check_password(request.POST.get('password', '')):
            messages.error(request, 'La contraseña no es correcta.')
        else:
            user = request.user
            email = user.email
            nombre = user.get_full_name().strip()
            username = user.username
            enviar_email_cuenta_eliminada(email=email, nombre=nombre, username=username)
            logout(request)
            user.delete()
            messages.success(request, 'Tu cuenta y sus datos fueron eliminados definitivamente.')
            return redirect('home')

    return render(request, 'usuarios/eliminar_cuenta.html', {
        'frase_confirmacion': FRASE_ELIMINAR_CUENTA,
    })


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
