from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from apps.productos.models import Producto
import os

class Command(BaseCommand):
    help = 'Depurar configuración de archivos media'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Depurando configuración de archivos media...")
        
        # Mostrar configuración actual
        self.stdout.write("=" * 60)
        self.stdout.write("⚙️  CONFIGURACIÓN ACTUAL:")
        self.stdout.write(f"   MEDIA_URL: {settings.MEDIA_URL}")
        self.stdout.write(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
        self.stdout.write(f"   Storage: {default_storage.__class__.__name__}")
        self.stdout.write(f"   DEBUG: {settings.DEBUG}")
        
        # Verificar WhiteNoise
        if 'whitenoise.middleware.WhiteNoiseMiddleware' in settings.MIDDLEWARE:
            self.stdout.write("   WhiteNoise: ✅ ACTIVADO")
        else:
            self.stdout.write("   WhiteNoise: ❌ NO ACTIVADO")
        
        # Verificar URLs
        self.stdout.write("=" * 60)
        self.stdout.write("🌐 VERIFICACIÓN DE URLs:")
        
        productos = Producto.objects.all()[:3]  # Solo primeros 3
        for producto in productos:
            if producto.imagen:
                url_generada = producto.imagen.url
                self.stdout.write(f"   📋 {producto.nombre}:")
                self.stdout.write(f"      🖼️ Archivo: {producto.imagen.name}")
                self.stdout.write(f"      🔗 URL: {url_generada}")
                
                # Verificar si existe en storage
                existe = default_storage.exists(producto.imagen.name)
                self.stdout.write(f"      {'✅ EXISTE' if existe else '❌ NO EXISTE'}")
                
                # Construir URL completa
                if url_generada.startswith('/'):
                    url_completa = url_generada
                else:
                    url_completa = settings.MEDIA_URL + url_generada
                
                self.stdout.write(f"      🌐 URL completa: {url_completa}")
                self.stdout.write("")
        
        # Verificar directorio media
        self.stdout.write("=" * 60)
        self.stdout.write("📁 VERIFICACIÓN DE DIRECTORIOS:")
        
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            self.stdout.write(f"   📁 MEDIA_ROOT: ✅ EXISTE")
            self.stdout.write(f"   📂 Ruta: {media_root}")
            
            # Listar archivos
            try:
                for root, dirs, files in os.walk(media_root):
                    level = root.replace(media_root, '').count(os.sep)
                    indent = ' ' * 2 * level
                    self.stdout.write(f'   {indent}{os.path.basename(root)}/')
                    
                    for file in files:
                        if file.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                            self.stdout.write(f'   {indent}  📄 {file}')
            except Exception as e:
                self.stdout.write(f"   ❌ Error listando: {e}")
        else:
            self.stdout.write(f"   📁 MEDIA_ROOT: ❌ NO EXISTE")
            # Crearlo
            try:
                os.makedirs(media_root, exist_ok=True)
                self.stdout.write(f"   📁 MEDIA_ROOT: ✅ CREADO")
            except Exception as e:
                self.stdout.write(f"   ❌ Error creando: {e}")
        
        # Probar URL directa
        self.stdout.write("=" * 60)
        self.stdout.write("🧪 PRUEBA DE URL DIRECTA:")
        
        # Construir URL de prueba
        media_url = settings.MEDIA_URL
        if not media_url.endswith('/'):
            media_url += '/'
        
        test_url = f"{media_url}productos/"
        self.stdout.write(f"   🌐 URL base: {test_url}")
        
        # Sugerencias
        self.stdout.write("=" * 60)
        self.stdout.write("🔧 SOLUCIONES POSIBLES:")
        self.stdout.write("   1. Verificar que MEDIA_ROOT sea accesible")
        self.stdout.write("   2. Asegurar que WhiteNoise sirva archivos media")
        self.stdout.write("   3. Revisar permisos del directorio media")
        self.stdout.write("   4. Verificar que las imágenes se suban correctamente")
        self.stdout.write("   5. Probar con collectstatic si es necesario")
        
        self.stdout.write("=" * 60)
        self.stdout.write("🎉 DEPURACIÓN COMPLETADA")
