from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sessions.models import Session

def admin_acceso_directo(request):
    """Acceso DIRECTO al admin sin login normal"""
    
    if request.method == 'POST':
        username = request.POST.get('username', 'admin')
        password = request.POST.get('password', 'perfumeria123')
        
        try:
            # MÉTODO 1: Autenticación normal
            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Login normal
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'message': 'Login normal exitoso',
                    'redirect': '/admin/',
                    'method': 'normal'
                })
            
            # MÉTODO 2: Forzar login si autenticación falla
            try:
                user = User.objects.get(username=username)
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Login forzado exitoso',
                    'redirect': '/admin/',
                    'method': 'forced'
                })
            except User.DoesNotExist:
                pass
            
            # MÉTODO 3: Crear usuario si no existe
            if username == 'admin':
                try:
                    user = User.objects.create_user(
                        username='admin',
                        email='gilbertandeliz04@gmail.com',
                        password='perfumeria123',
                        is_superuser=True,
                        is_staff=True,
                        is_active=True
                    )
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Usuario creado y login exitoso',
                        'redirect': '/admin/',
                        'method': 'created'
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': f'Error al crear usuario: {str(e)}'
                    })
            
            return JsonResponse({
                'success': False,
                'error': 'Credenciales incorrectas'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error del sistema: {str(e)}'
            })
    
    return render(request, 'admin_acceso_directo.html')

@csrf_exempt
def admin_acceso_inmediato(request):
    """Acceso INMEDIATO sin ninguna validación"""
    if request.method == 'POST':
        try:
            # Crear o obtener usuario admin
            user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'gilbertandeliz04@gmail.com',
                    'is_superuser': True,
                    'is_staff': True,
                    'is_active': True
                }
            )
            
            if created:
                user.set_password('perfumeria123')
                user.save()
            
            # Forzar login
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            
            return JsonResponse({
                'success': True,
                'message': 'Acceso inmediato exitoso',
                'redirect': '/admin/',
                'created': created
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error: {str(e)}'
            })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def admin_panel_publico(request):
    """Panel admin público que funciona sin login"""
    try:
        # Verificar si hay usuario admin
        admin_exists = User.objects.filter(username='admin', is_superuser=True).exists()
        
        context = {
            'admin_exists': admin_exists,
            'site_title': 'D.A.R.C.Y. Admin Panel',
            'message': 'Panel de administración accesible'
        }
        
        return render(request, 'admin_panel_publico.html', context)
        
    except Exception as e:
        return render(request, 'admin_panel_publico.html', {
            'error': str(e),
            'admin_exists': False
        })
