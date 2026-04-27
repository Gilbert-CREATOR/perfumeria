from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

class Command(BaseCommand):
    help = 'Crear admin estilo SQLite (como funcionaba antes)'

    def handle(self, *args, **options):
        self.stdout.write("🔐 Creando admin estilo SQLite (como funcionaba antes)...")
        
        try:
            with transaction.atomic():
                # Eliminar usuarios admin existentes
                User.objects.filter(username__in=['admin', 'superadmin']).delete()
                
                # Crear usuario admin exactamente como en SQLite
                admin = User.objects.create_superuser(
                    username='admin',
                    email='gilbertandeliz04@gmail.com',
                    password='perfumeria123',
                    first_name='Administrador',
                    last_name='Sistema'
                )
                
                # Verificar que se creó correctamente
                admin.refresh_from_db()
                
                self.stdout.write(self.style.SUCCESS(f'✅ Admin creado estilo SQLite:'))
                self.stdout.write(f'   👤 Usuario: {admin.username}')
                self.stdout.write(f'   📧 Email: {admin.email}')
                self.stdout.write(f'   🔐 Contraseña: perfumeria123')
                self.stdout.write(f'   ✅ Es superusuario: {admin.is_superuser}')
                self.stdout.write(f'   ✅ Es staff: {admin.is_staff}')
                self.stdout.write(f'   ✅ Activo: {admin.is_active}')
                
                # Test de autenticación
                from django.contrib.auth import authenticate
                test_user = authenticate(username='admin', password='perfumeria123')
                
                if test_user:
                    self.stdout.write(self.style.SUCCESS('✅ Autenticación verificada - Login funcionará'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  Autenticación falló, pero usuario creado'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
            return
        
        self.stdout.write("=" * 60)
        self.stdout.write("🚀 Configuración estilo SQLite aplicada:")
        self.stdout.write("   📍 URL: https://perfumeria-darcy.onrender.com/admin/")
        self.stdout.write("   👤 Usuario: admin")
        self.stdout.write("   🔐 Contraseña: perfumeria123")
        self.stdout.write("=" * 60)
        self.stdout.write("🎉 ¡Admin configurado como cuando usabas SQLite!")
