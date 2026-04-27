from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Crear superusuario administrador para Perfumería D.A.R.C.Y.'

    def handle(self, *args, **options):
        self.stdout.write("🔐 Creando superusuario administrador...")
        
        try:
            # Si el usuario ya existe, eliminarlo y recrearlo
            if User.objects.filter(username='admin').exists():
                self.stdout.write(self.style.WARNING('⚠️  El usuario admin ya existe, eliminando y recreando...'))
                User.objects.filter(username='admin').delete()
            
            # Crear superusuario
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
            self.stdout.write(f'   🌐 Acceso: /admin/')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al crear superusuario: {str(e)}'))
        
        self.stdout.write("=" * 50)
        self.stdout.write("🚀 Puedes acceder al panel administrativo:")
        self.stdout.write("   📍 URL: https://perfumeria-darcy.onrender.com/admin/")
        self.stdout.write("   👤 Usuario: admin")
        self.stdout.write("   🔐 Contraseña: perfumeria123")
        self.stdout.write("=" * 50)
