from django.apps import AppConfig

class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.usuarios'
    
    def ready(self):
        """Importar señales cuando la aplicación esté lista"""
        import apps.usuarios.signals
