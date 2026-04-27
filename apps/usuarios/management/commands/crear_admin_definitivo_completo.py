from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib.auth import authenticate
import hashlib

class Command(BaseCommand):
    help = 'SOLUCIÓN DEFINITIVA COMPLETA: Crear admin con todos los métodos posibles'

    def handle(self, *args, **options):
        self.stdout.write("🔥 SOLUCIÓN DEFINITIVA COMPLETA: Creando admin...")
        
        success = False
        attempts = []
        
        # MÉTODO 1: create_superuser estándar
        try:
            self.stdout.write("📋 Método 1: create_superuser estándar...")
            with transaction.atomic():
                User.objects.filter(username='admin').delete()
                admin = User.objects.create_superuser(
                    username='admin',
                    email='gilbertandeliz04@gmail.com',
                    password='perfumeria123'
                )
                
                # Verificar
                test_auth = authenticate(username='admin', password='perfumeria123')
                if test_auth:
                    attempts.append("✅ Método 1: create_superuser - EXITOSO")
                    success = True
                else:
                    attempts.append("❌ Método 1: create_superuser - Autenticación falló")
        except Exception as e:
            attempts.append(f"❌ Método 1: create_superuser - Error: {str(e)}")
        
        # MÉTODO 2: create_user + manual superuser
        if not success:
            try:
                self.stdout.write("📋 Método 2: create_user + manual superuser...")
                with transaction.atomic():
                    User.objects.filter(username='admin').delete()
                    user = User.objects.create_user(
                        username='admin',
                        email='gilbertandeliz04@gmail.com',
                        password='perfumeria123'
                    )
                    user.is_superuser = True
                    user.is_staff = True
                    user.is_active = True
                    user.save()
                    
                    # Verificar
                    test_auth = authenticate(username='admin', password='perfumeria123')
                    if test_auth:
                        attempts.append("✅ Método 2: create_user + manual - EXITOSO")
                        success = True
                    else:
                        attempts.append("❌ Método 2: create_user + manual - Autenticación falló")
            except Exception as e:
                attempts.append(f"❌ Método 2: create_user + manual - Error: {str(e)}")
        
        # MÉTODO 3: Sin contraseña hash directo
        if not success:
            try:
                self.stdout.write("📋 Método 3: Sin contraseña hash directo...")
                with transaction.atomic():
                    User.objects.filter(username='admin').delete()
                    user = User.objects.create_user(
                        username='admin',
                        email='gilbertandeliz04@gmail.com',
                        password='perfumeria123'
                    )
                    user.is_superuser = True
                    user.is_staff = True
                    user.save()
                    
                    # Forzar refresh
                    user.refresh_from_db()
                    
                    # Verificar
                    test_auth = authenticate(username='admin', password='perfumeria123')
                    if test_auth:
                        attempts.append("✅ Método 3: Sin contraseña hash - EXITOSO")
                        success = True
                    else:
                        attempts.append("❌ Método 3: Sin contraseña hash - Autenticación falló")
            except Exception as e:
                attempts.append(f"❌ Método 3: Sin contraseña hash - Error: {str(e)}")
        
        # MÉTODO 4: Crear múltiples usuarios de prueba
        if not success:
            try:
                self.stdout.write("📋 Método 4: Crear múltiples usuarios de prueba...")
                with transaction.atomic():
                    # Limpiar todos
                    User.objects.filter(username__in=['admin', 'superadmin', 'root']).delete()
                    
                    # Crear admin
                    admin1 = User.objects.create_user(
                        username='admin',
                        email='admin@test.com',
                        password='perfumeria123',
                        is_superuser=True,
                        is_staff=True
                    )
                    
                    # Crear superadmin
                    admin2 = User.objects.create_user(
                        username='superadmin',
                        email='super@test.com',
                        password='admin123',
                        is_superuser=True,
                        is_staff=True
                    )
                    
                    # Verificar ambos
                    auth1 = authenticate(username='admin', password='perfumeria123')
                    auth2 = authenticate(username='superadmin', password='admin123')
                    
                    if auth1 or auth2:
                        attempts.append("✅ Método 4: Múltiples usuarios - EXITOSO")
                        success = True
                        if auth1:
                            attempts.append("   ✅ admin/perfumeria123 funciona")
                        if auth2:
                            attempts.append("   ✅ superadmin/admin123 funciona")
                    else:
                        attempts.append("❌ Método 4: Múltiples usuarios - Autenticación falló")
            except Exception as e:
                attempts.append(f"❌ Método 4: Múltiples usuarios - Error: {str(e)}")
        
        # MÉTODO 5: Verificación final y debugging
        try:
            self.stdout.write("📋 Método 5: Verificación final...")
            
            # Listar todos los usuarios
            all_users = User.objects.all()
            self.stdout.write(f"📊 Total de usuarios: {all_users.count()}")
            
            for user in all_users:
                self.stdout.write(f"   👤 {user.username} (Superuser: {user.is_superuser}, Staff: {user.is_staff}, Active: {user.is_active})")
            
            # Intentar autenticar con admin
            final_auth = authenticate(username='admin', password='perfumeria123')
            if final_auth:
                attempts.append("✅ Método 5: Verificación final - EXITOSO")
                success = True
            else:
                attempts.append("❌ Método 5: Verificación final - Autenticación falló")
                
        except Exception as e:
            attempts.append(f"❌ Método 5: Verificación final - Error: {str(e)}")
        
        # RESULTADOS
        self.stdout.write("=" * 70)
        self.stdout.write("📊 RESULTADOS DE TODOS LOS INTENTOS:")
        for attempt in attempts:
            self.stdout.write(attempt)
        
        if success:
            self.stdout.write("=" * 70)
            self.stdout.write("🎉 ¡AL MENOS UN MÉTODO FUNCIONÓ!")
            self.stdout.write("🚀 Puedes intentar iniciar sesión con:")
            self.stdout.write("   👤 Opción 1: admin / perfumeria123")
            self.stdout.write("   👤 Opción 2: superadmin / admin123")
            self.stdout.write("   📍 URL: https://perfumeria-darcy.onrender.com/admin/")
            self.stdout.write("=" * 70)
        else:
            self.stdout.write("=" * 70)
            self.stdout.write("❌ NINGÚN MÉTODO FUNCIONÓ - Hay un problema fundamental")
            self.stdout.write("🔍 Revisa los logs del deploy para más detalles")
            self.stdout.write("=" * 70)
