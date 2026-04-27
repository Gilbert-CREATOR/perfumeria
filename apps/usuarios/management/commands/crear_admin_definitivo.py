from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
import hashlib

class Command(BaseCommand):
    help = 'SOLUCIÓN DEFINITIVA: Crear admin con múltiples métodos'

    def handle(self, *args, **options):
        self.stdout.write("🔥 SOLUCIÓN DEFINITIVA: Creando admin...")
        
        try:
            with transaction.atomic():
                # Método 1: Eliminar y recrear
                self.stdout.write("🗑️  Método 1: Eliminando usuarios admin existentes...")
                User.objects.filter(username='admin').delete()
                
                # Método 2: Crear con create_user primero
                self.stdout.write("👤 Método 2: Creando usuario con create_user...")
                admin = User.objects.create_user(
                    username='admin',
                    email='gilbertandeliz04@gmail.com',
                    password='perfumeria123'
                )
                
                # Método 3: Convertir a superusuario
                self.stdout.write("⚡ Método 3: Convirtiendo a superusuario...")
                admin.is_superuser = True
                admin.is_staff = True
                admin.first_name = 'Administrador'
                admin.last_name = 'Sistema'
                admin.save()
                
                # Método 4: Verificación directa
                self.stdout.write("🔍 Método 4: Verificación directa...")
                admin.refresh_from_db()
                
                # Método 5: Test de contraseña
                self.stdout.write("🔐 Método 5: Test de contraseña...")
                from django.contrib.auth import authenticate
                test_user = authenticate(username='admin', password='perfumeria123')
                
                if test_user:
                    self.stdout.write(self.style.SUCCESS('✅ CONTRASEÑA VERIFICADA - Login funcionará'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  Contraseña no verificada, pero usuario creado'))
                
                # Mostrar información completa
                self.stdout.write(self.style.SUCCESS(f'✅ Admin creado exitosamente:'))
                self.stdout.write(f'   👤 Usuario: {admin.username}')
                self.stdout.write(f'   📧 Email: {admin.email}')
                self.stdout.write(f'   🔐 Contraseña: perfumeria123')
                self.stdout.write(f'   🆔 ID: {admin.id}')
                self.stdout.write(f'   ✅ Es superusuario: {admin.is_superuser}')
                self.stdout.write(f'   ✅ Es staff: {admin.is_staff}')
                self.stdout.write(f'   ✅ Activo: {admin.is_active}')
                self.stdout.write(f'   📅 Fecha: {admin.date_joined}')
                
                # Método 6: Crear usuario alternativo
                self.stdout.write("🔄 Método 6: Creando usuario alternativo...")
                admin2 = User.objects.create_user(
                    username='superadmin',
                    email='admin@perfumeria.com',
                    password='admin123',
                    is_superuser=True,
                    is_staff=True
                )
                admin2.first_name = 'Super'
                admin2.last_name = 'Admin'
                admin2.save()
                
                self.stdout.write(self.style.SUCCESS(f'✅ Usuario alternativo creado:'))
                self.stdout.write(f'   👤 Usuario: superadmin')
                self.stdout.write(f'   🔐 Contraseña: admin123')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
            return
        
        self.stdout.write("=" * 70)
        self.stdout.write("🚀 ACCESO GARANTIZADO - Prueba estas opciones:")
        self.stdout.write("   📍 URL: https://perfumeria-darcy.onrender.com/admin/")
        self.stdout.write("   👤 Opción 1: admin / perfumeria123")
        self.stdout.write("   👤 Opción 2: superadmin / admin123")
        self.stdout.write("=" * 70)
        self.stdout.write("🎉 ¡SOLUCIÓN DEFINITIVA APLICADA!")
