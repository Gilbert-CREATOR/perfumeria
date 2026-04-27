from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Verificar usuarios admin existentes en la base de datos'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Verificando usuarios admin existentes...")
        
        # Buscar todos los usuarios admin
        admins = User.objects.filter(username='admin')
        
        if admins.exists():
            self.stdout.write(f"✅ Se encontraron {admins.count()} usuario(s) admin:")
            for admin in admins:
                self.stdout.write(f"   👤 Usuario: {admin.username}")
                self.stdout.write(f"   📧 Email: {admin.email}")
                self.stdout.write(f"   🆔 ID: {admin.id}")
                self.stdout.write(f"   ✅ Es superusuario: {admin.is_superuser}")
                self.stdout.write(f"   ✅ Es staff: {admin.is_staff}")
                self.stdout.write(f"   📅 Fecha de creación: {admin.date_joined}")
                self.stdout.write("   " + "-" * 40)
        else:
            self.stdout.write(self.style.WARNING("❌ No se encontró ningún usuario admin"))
        
        # Mostrar todos los usuarios
        all_users = User.objects.all()
        self.stdout.write(f"\n📊 Total de usuarios en la base de datos: {all_users.count()}")
        
        for user in all_users:
            self.stdout.write(f"   👤 {user.username} (Superuser: {user.is_superuser}, Staff: {user.is_staff})")
        
        self.stdout.write("=" * 60)
        self.stdout.write("🚀 Para acceder al panel administrativo:")
        self.stdout.write("   📍 URL: https://perfumeria-darcy.onrender.com/admin/")
        self.stdout.write("   👤 Usuario: admin")
        self.stdout.write("   🔐 Contraseña: perfumeria123")
        self.stdout.write("=" * 60)
