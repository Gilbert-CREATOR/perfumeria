from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test

def admin_bypass_login(request):
    """BYPASS COMPLETO: Login directo al admin sin verificación"""
    
    if request.method == 'POST':
        username = request.POST.get('username', 'admin')
        password = request.POST.get('password', 'perfumeria123')
        
        # Intentar autenticación normal
        user = authenticate(username=username, password=password)
        
        if user is None:
            # BYPASS: Si la autenticación falla, crear usuario temporal
            try:
                user = User.objects.get(username='admin')
                # Forzar login sin contraseña
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                
                return JsonResponse({
                    'success': True,
                    'message': 'BYPASS: Login forzado exitoso',
                    'redirect': '/admin/'
                })
            except User.DoesNotExist:
                # Crear usuario admin si no existe
                user = User.objects.create_user(
                    username='admin',
                    email='admin@perfumeria.com',
                    password='perfumeria123',
                    is_superuser=True,
                    is_staff=True
                )
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                
                return JsonResponse({
                    'success': True,
                    'message': 'BYPASS: Usuario creado y login forzado',
                    'redirect': '/admin/'
                })
        
        # Si la autenticación normal funcionó
        if user.is_superuser or user.is_staff:
            login(request, user)
            return JsonResponse({
                'success': True,
                'message': 'Login normal exitoso',
                'redirect': '/admin/'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Usuario no es administrador'
            })
    
    return render(request, 'admin_bypass.html')

@user_passes_test(lambda u: u.is_superuser, login_url='/admin-bypass/')
def admin_direct_access(request):
    """Acceso directo al admin si ya es superusuario"""
    return redirect('/admin/')

@csrf_exempt
def create_admin_emergency(request):
    """Crear admin de emergencia sin validaciones"""
    if request.method == 'POST':
        try:
            # Eliminar todos los usuarios admin existentes
            User.objects.filter(username__in=['admin', 'superadmin']).delete()
            
            # Crear nuevo admin
            admin = User.objects.create_user(
                username='admin',
                email='admin@perfumeria.com',
                password='perfumeria123',
                is_superuser=True,
                is_staff=True,
                is_active=True
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Admin de emergencia creado',
                'username': 'admin',
                'password': 'perfumeria123'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
