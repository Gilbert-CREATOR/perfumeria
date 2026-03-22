from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.carrito.models import PerfilUsuario

class Command(BaseCommand):
    help = 'Crear perfiles para usuarios existentes'

    def handle(self, *args, **options):
        self.stdout.write("=" * 50)
        self.stdout.write("CREANDO PERFILES DE USUARIO")
        self.stdout.write("=" * 50)
        
        usuarios_sin_perfil = User.objects.filter(perfil__isnull=True)
        total_usuarios = usuarios_sin_perfil.count()
        
        if total_usuarios == 0:
            self.stdout.write("✅ Todos los usuarios ya tienen perfil")
            return
        
        self.stdout.write(f"Encontrados {total_usuarios} usuarios sin perfil:")
        
        creados = 0
        for usuario in usuarios_sin_perfil:
            # Determinar tipo de usuario basado en is_staff
            if usuario.is_staff:
                tipo_usuario = 'admin'
            else:
                tipo_usuario = 'cliente'
            
            # Crear perfil
            perfil = PerfilUsuario.objects.create(
                usuario=usuario,
                tipo_usuario=tipo_usuario
            )
            
            creados += 1
            self.stdout.write(f"  ✅ {usuario.username} -> {tipo_usuario}")
        
        self.stdout.write("=" * 50)
        self.stdout.write(f"✅ Se crearon {creados} perfiles exitosamente")
        self.stdout.write("=" * 50)
