from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required

def home(request):
    """Vista home"""
    from apps.productos.models import Producto
    productos_destacados = Producto.objects.filter(disponible=True)[:6]
    return render(request, 'home.html', {'productos_destacados': productos_destacados})

@csrf_exempt
@require_http_methods(["GET", "POST"])
def emergencia_admin(request):
    """VISTA DE EMERGENCIA: Acceso directo al admin sin login"""
    
    if request.method == 'POST':
        # Crear usuario admin si no existe
        try:
            admin, created = User.objects.get_or_create(
                username='emergencia_admin',
                defaults={
                    'email': 'emergency@admin.com',
                    'is_superuser': True,
                    'is_staff': True,
                    'first_name': 'Emergency',
                    'last_name': 'Admin'
                }
            )
            
            if created:
                admin.set_password('emergencia123')
                admin.save()
                message = "✅ Usuario de emergencia creado"
            else:
                message = "✅ Usuario de emergencia ya existe"
            
            # Login automático
            login(request, admin)
            
            return JsonResponse({
                'success': True,
                'message': message,
                'redirect': '/admin/'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    # GET: Mostrar página de emergencia
    return render(request, 'emergencia_admin.html')

@csrf_exempt
def crear_usuario_emergencia(request):
    """Crear usuario de emergencia via API"""
    if request.method == 'POST':
        try:
            # Eliminar usuarios existentes
            User.objects.filter(username__in=['admin', 'superadmin', 'emergencia_admin']).delete()
            
            # Crear nuevo usuario
            user = User.objects.create_user(
                username='emergencia_admin',
                email='emergency@admin.com',
                password='emergencia123',
                is_superuser=True,
                is_staff=True
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Usuario creado exitosamente',
                'username': 'emergencia_admin',
                'password': 'emergencia123'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
