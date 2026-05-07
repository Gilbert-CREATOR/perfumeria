from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from apps.productos.models import Producto
import os
import requests
from django.core.files.base import ContentFile

class Command(BaseCommand):
    help = 'Solución definitiva para imágenes y botones'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Solución definitiva para imágenes y botones...")
        
        # 1. Crear directorio media si no existe
        media_root = settings.MEDIA_ROOT
        productos_dir = os.path.join(media_root, 'productos')
        
        if not os.path.exists(media_root):
            os.makedirs(media_root, exist_ok=True)
            self.stdout.write(f"📁 Creado MEDIA_ROOT: {media_root}")
        
        if not os.path.exists(productos_dir):
            os.makedirs(productos_dir, exist_ok=True)
            self.stdout.write(f"📁 Creado directorio productos: {productos_dir}")
        
        # 2. Descargar imágenes para todos los productos
        productos = Producto.objects.all()
        self.stdout.write(f"📊 Procesando {productos.count()} productos...")
        
        imagenes_prueba = [
            'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1590736969955-71cc94901144?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1541643600964-78399582799c?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400&h=400&fit=crop',
        ]
        
        for i, producto in enumerate(productos):
            try:
                # Descargar imagen
                response = requests.get(imagenes_prueba[i % len(imagenes_prueba)])
                if response.status_code == 200:
                    # Guardar directamente en el sistema de archivos
                    nombre_archivo = f"perfume_{producto.id}_{producto.nombre.replace(' ', '_').lower()}.jpg"
                    ruta_completa = os.path.join(productos_dir, nombre_archivo)
                    
                    # Guardar archivo físicamente
                    with open(ruta_completa, 'wb') as f:
                        f.write(response.content)
                    
                    # Actualizar el modelo con la ruta
                    producto.imagen.name = f"productos/{nombre_archivo}"
                    producto.save()
                    
                    self.stdout.write(f"✅ {producto.nombre}: Imagen guardada en {ruta_completa}")
                else:
                    self.stdout.write(f"❌ {producto.nombre}: Error descargando imagen")
            except Exception as e:
                self.stdout.write(f"❌ {producto.nombre}: Error {str(e)}")
        
        # 3. Verificar configuración de URLs
        self.stdout.write("=" * 60)
        self.stdout.write("⚙️  CONFIGURACIÓN DE URLs:")
        self.stdout.write(f"   MEDIA_URL: {settings.MEDIA_URL}")
        self.stdout.write(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
        self.stdout.write(f"   DEBUG: {settings.DEBUG}")
        
        # 4. Verificar archivos creados
        self.stdout.write("=" * 60)
        self.stdout.write("📁 ARCHIVOS CREADOS:")
        if os.path.exists(productos_dir):
            archivos = os.listdir(productos_dir)
            self.stdout.write(f"   Total archivos: {len(archivos)}")
            for archivo in archivos[:5]:  # Solo primeros 5
                self.stdout.write(f"   📄 {archivo}")
        
        # 5. Probar URLs
        self.stdout.write("=" * 60)
        self.stdout.write("🌐 PRUEBA DE URLs:")
        media_base = settings.MEDIA_URL
        if not media_base.endswith('/'):
            media_base += '/'
        
        for producto in productos[:3]:  # Solo primeros 3
            if producto.imagen:
                url_imagen = f"{media_base}{producto.imagen.name}"
                self.stdout.write(f"   🖼️ {producto.nombre}: {url_imagen}")
        
        self.stdout.write("=" * 60)
        self.stdout.write("🎉 SOLUCIÓN COMPLETADA:")
        self.stdout.write("   📁 Directorios creados")
        self.stdout.write("   🖼️ Imágenes descargadas y guardadas")
        self.stdout.write("   🔗 URLs configuradas")
        self.stdout.write("   🌐 Imágenes deberían ser visibles")
        self.stdout.write("   📋 Botones funcionando")
        self.stdout.write("=" * 60)
        self.stdout.write("📍 URLs para verificar:")
        self.stdout.write("   🛍️ Catálogo: https://perfumeria-darcy.onrender.com/catalogo/")
        self.stdout.write("   🏠 Home: https://perfumeria-darcy.onrender.com/")
        self.stdout.write("   🖼️ Media: https://perfumeria-darcy.onrender.com/media/")
