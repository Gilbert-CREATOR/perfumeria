from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from apps.carrito.models import Pedido
from apps.productos.models import Favorito
from .models import PerfilUsuario, Direccion
from .forms import DireccionForm, LoginSeguroForm, PerfilForm, RegistroSeguroForm
from django.contrib import messages
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.core import signing
from django.contrib.auth import views as auth_views
from django.contrib.auth.hashers import check_password, make_password
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
import hashlib
from datetime import timedelta

from apps.carrito.services import complete_pending_cart_item
from .emails import VERIFICACION_SALT, enviar_email_bienvenida, enviar_email_cuenta_eliminada


FRASE_ELIMINAR_CUENTA = 'ELIMINAR MI CUENTA'
CREDENCIALES_INVALIDAS = 'Email o usuario o contraseña incorrecta.'
MAX_INTENTOS_LOGIN = getattr(settings, 'LOGIN_MAX_FAILED_ATTEMPTS', 5)
BLOQUEO_LOGIN_SEGUNDOS = getattr(settings, 'LOGIN_LOCKOUT_SECONDS', 15 * 60)
# Mantiene un coste de hash similar aunque la cuenta no exista, reduciendo las
# diferencias de tiempo que podrían usarse para enumerar usuarios.
PASSWORD_FALSA_HASH = make_password('darcy-comprobacion-login')


def _ip_cliente(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return (forwarded.split(',')[0] if forwarded else request.META.get('REMOTE_ADDR', '')).strip()


def _clave_intentos(request, credencial):
    material = f'{_ip_cliente(request)}:{credencial.casefold()}'.encode('utf-8')
    return 'login-attempt:' + hashlib.sha256(material).hexdigest()


def _perfil_bloqueado(user):
    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=user)
    if perfil.bloqueado_hasta and perfil.bloqueado_hasta <= timezone.now():
        perfil.intentos_login_fallidos = 0
        perfil.bloqueado_hasta = None
        perfil.save(update_fields=['intentos_login_fallidos', 'bloqueado_hasta'])
        return False
    return perfil.esta_bloqueado()


def _registrar_fallo_cuenta(user):
    """Incremento atómico para que peticiones simultáneas no evadan el bloqueo."""
    with transaction.atomic():
        perfil, _ = PerfilUsuario.objects.select_for_update().get_or_create(usuario=user)
        if perfil.bloqueado_hasta and perfil.bloqueado_hasta <= timezone.now():
            perfil.intentos_login_fallidos = 0
            perfil.bloqueado_hasta = None
        perfil.intentos_login_fallidos += 1
        if perfil.intentos_login_fallidos >= MAX_INTENTOS_LOGIN:
            perfil.bloqueado_hasta = timezone.now() + timedelta(seconds=BLOQUEO_LOGIN_SEGUNDOS)
        perfil.save(update_fields=['intentos_login_fallidos', 'bloqueado_hasta'])


def _limpiar_fallos_cuenta(user):
    PerfilUsuario.objects.filter(usuario=user).update(
        intentos_login_fallidos=0,
        bloqueado_hasta=None,
    )


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


@sensitive_post_parameters('password')
def login_usuario(request):
    if request.user.is_authenticated:
        return redirect('/')
        
    if request.method == 'POST':
        form = LoginSeguroForm({
            'credencial': request.POST.get('username', ''),
            'password': request.POST.get('password', ''),
        })
        if not form.is_valid():
            messages.error(request, CREDENCIALES_INVALIDAS)
            return render(request, 'usuarios/login.html')

        login_field = form.cleaned_data['credencial']
        password = form.cleaned_data['password']
        attempt_key = _clave_intentos(request, login_field)
        intentos = cache.get(attempt_key, 0)
        if intentos >= MAX_INTENTOS_LOGIN:
            messages.error(request, CREDENCIALES_INVALIDAS)
            return render(request, 'usuarios/login.html')

        user_obj = User.objects.filter(username__iexact=login_field).order_by('id').first()
        if user_obj is None:
            user_obj = User.objects.filter(email__iexact=login_field).order_by('id').first()
        username = user_obj.username if user_obj else None

        if username:
            user = authenticate(request, username=username, password=password)
        else:
            check_password(password, PASSWORD_FALSA_HASH)
            user = None

        cuenta_bloqueada = bool(user_obj and _perfil_bloqueado(user_obj))

        if user and not cuenta_bloqueada:
            cache.delete(attempt_key)
            _limpiar_fallos_cuenta(user)
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
            cache.set(attempt_key, intentos + 1, timeout=BLOQUEO_LOGIN_SEGUNDOS)
            if user_obj and not cuenta_bloqueada:
                _registrar_fallo_cuenta(user_obj)
            messages.error(request, CREDENCIALES_INVALIDAS)

    return render(request, 'usuarios/login.html')


@require_POST
def logout_usuario(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente')
    return redirect('/')


@sensitive_post_parameters('password1', 'password2')
def registro_usuario(request):
    if request.user.is_authenticated:
        return redirect('/')
        
    if request.method == 'POST':
        form = RegistroSeguroForm(request.POST)
        if not form.is_valid():
            for errores in form.errors.values():
                for error in errores:
                    messages.error(request, error)
            return render(request, 'usuarios/register.html', {'form': form})
        
        try:
            with transaction.atomic():
                user = form.save()
        except IntegrityError:
            messages.error(request, 'No se pudo crear la cuenta con esos datos.')
            return render(request, 'usuarios/register.html', {'form': form})
        
        user = authenticate(
            request,
            username=user.username,
            password=form.cleaned_data['password1'],
        )
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


@method_decorator(sensitive_post_parameters('email'), name='dispatch')
class DarcyPasswordResetView(auth_views.PasswordResetView):
    template_name = 'usuarios/password_reset.html'
    email_template_name = 'emails/password_reset.txt'
    html_email_template_name = 'emails/password_reset.html'
    subject_template_name = 'emails/password_reset_subject.txt'

    def post(self, request, *args, **kwargs):
        key = 'password-reset:' + hashlib.sha256(_ip_cliente(request).encode()).hexdigest()
        intentos = cache.get(key, 0)
        if intentos >= 3:
            # Misma respuesta haya o no una cuenta: evita enumeración y abuso de correo.
            return redirect(self.get_success_url())
        cache.set(key, intentos + 1, timeout=15 * 60)
        return super().post(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        site_url = getattr(settings, 'PUBLIC_SITE_URL', 'http://localhost:8000').rstrip('/')
        self.extra_email_context = {
            'site_url': site_url,
            'catalogo_url': f'{site_url}{reverse("catalogo")}',
        }
        return super().dispatch(request, *args, **kwargs)


@login_required
@sensitive_post_parameters('password')
def eliminar_cuenta(request):
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Las cuentas administrativas no se eliminan desde esta opción.')
        return redirect('perfil')

    if request.method == 'POST':
        username_confirmacion = request.POST.get('username_confirmacion', '').strip()
        frase_confirmacion = request.POST.get('frase_confirmacion', '').strip()

        if username_confirmacion != request.user.username:
            messages.error(request, 'No se pudo confirmar la identidad con esos datos.')
        elif frase_confirmacion != FRASE_ELIMINAR_CUENTA:
            messages.error(request, f'Escribe exactamente: {FRASE_ELIMINAR_CUENTA}')
        elif not request.user.check_password(request.POST.get('password', '')):
            messages.error(request, 'No se pudo confirmar la identidad con esos datos.')
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
