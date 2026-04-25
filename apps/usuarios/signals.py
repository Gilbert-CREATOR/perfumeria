from django.db.models.signals import post_migrate
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.conf import settings

@receiver(post_migrate)
def create_admin_user(sender, **kwargs):
    """
    Crear superusuario admin automáticamente después de las migraciones
    """
    # Solo ejecutar en producción
    if not settings.DEBUG:
        User = get_user_model()
        try:
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser(
                    username='admin',
                    email='gilbertandeliz04@gmail.com',
                    password='perfumeria123',
                    first_name='Administrador',
                    last_name='Sistema'
                )
                print("✅ Superusuario admin creado automáticamente en producción")
            else:
                print("📋 El superusuario admin ya existe")
        except Exception as e:
            print(f"⚠️ Error creando superusuario: {e}")
