from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

class Command(BaseCommand):
    help = 'Forzar creación de superusuario administrador - BORRA Y RECREA'

    def handle(self, *args, **options):
        self.stdout.write("🔐 FORZANDO creación de superusuario administrador...")
        
        try:
            with transaction.atomic():
                # Eliminar TODOS los usuarios admin si existen
                admins = User.objects.filter(username='admin')
                if admins.exists():
                    self.stdout.write(f"⚠️  Eliminando {admins.count()} usuario(s) admin existentes...")
                    admins.delete()
                
                # Crear nuevo superusuario
                admin = User.objects.create_superuser(
                    username='admin',
                    email='gilbertandeliz04@gmail.com',
                    password='perfumeria123',
                    first_name='Administrador',
                    last_name='Sistema'
                )
                
                self.stdout.write(self.style.SUCCESS(f'✅ Superusuario creado exitosamente:'))
                self.stdout.write(f'   👤 Usuario: {admin.username}')
                self.stdout.write(f'   📧 Email: {admin.email}')
                self.stdout.write(f'   🔐 Contraseña: perfumeria123')
                self.stdout.write(f'   🆔 ID: {admin.id}')
                self.stdout.write(f'   ✅ Es superusuario: {admin.is_superuser}')
                self.stdout.write(f'   ✅ Es staff: {admin.is_staff}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al crear superusuario: {str(e)}'))
            return
        
        self.stdout.write("=" * 60)
        self.stdout.write("🚀 Puedes acceder al panel administrativo:")
        self.stdout.write("   📍 URL: https://perfumeria-darcy.onrender.com/admin/")
        self.stdout.write("   👤 Usuario: admin")
        self.stdout.write("   🔐 Contraseña: perfumeria123")
        self.stdout.write("=" * 60)
        self.stdout.write("🎉 ¡Usuario admin FORZADO y listo para usar!")
