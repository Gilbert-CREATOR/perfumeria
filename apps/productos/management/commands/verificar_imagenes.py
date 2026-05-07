from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from apps.productos.models import Producto
import os

class Command(BaseCommand):
    help = 'Verificar estado de las imágenes de productos'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Verificando imágenes de productos...")
        
        productos = Producto.objects.all()
        total_productos = productos.count()
        productos_con_imagen = 0
        productos_sin_imagen = 0
        imagenes_existentes = 0
        imagenes_faltantes = 0
        
        for producto in productos:
            if producto.imagen:
                productos_con_imagen += 1
                # Verificar si el archivo existe en el storage
                if default_storage.exists(producto.imagen.name):
                    imagenes_existentes += 1
                    self.stdout.write(f"✅ {producto.nombre}: {producto.imagen.name} - EXISTE")
                else:
                    imagenes_faltantes += 1
                    self.stdout.write(f"❌ {producto.nombre}: {producto.imagen.name} - NO EXISTE")
            else:
                productos_sin_imagen += 1
                self.stdout.write(f"⚠️  {producto.nombre}: SIN IMAGEN")
        
        self.stdout.write("=" * 60)
        self.stdout.write("📊 RESUMEN:")
        self.stdout.write(f"   Total productos: {total_productos}")
        self.stdout.write(f"   Con imagen: {productos_con_imagen}")
        self.stdout.write(f"   Sin imagen: {productos_sin_imagen}")
        self.stdout.write(f"   Imágenes existentes: {imagenes_existentes}")
        self.stdout.write(f"   Imágenes faltantes: {imagenes_faltantes}")
        
        # Verificar configuración de media
        self.stdout.write("=" * 60)
        self.stdout.write("⚙️  CONFIGURACIÓN:")
        from django.conf import settings
        self.stdout.write(f"   MEDIA_URL: {settings.MEDIA_URL}")
        self.stdout.write(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
        self.stdout.write(f"   Storage: {default_storage.__class__.__name__}")
        
        # Verificar si directorio media existe
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            self.stdout.write(f"   Directorio media: ✅ EXISTE")
            # Listar archivos en media
            try:
                for root, dirs, files in os.walk(media_root):
                    for file in files:
                        if file.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                            rel_path = os.path.relpath(os.path.join(root, file), media_root)
                            self.stdout.write(f"   📁 {rel_path}")
            except Exception as e:
                self.stdout.write(f"   Error listando archivos: {e}")
        else:
            self.stdout.write(f"   Directorio media: ❌ NO EXISTE")
        
        self.stdout.write("=" * 60)
        if imagenes_faltantes > 0:
            self.stdout.write("🔧 ACCIONES RECOMENDADAS:")
            self.stdout.write("1. Verificar que las imágenes se suban correctamente")
            self.stdout.write("2. Revisar configuración de MEDIA_URL y MEDIA_ROOT")
            self.stdout.write("3. Ejecutar collectstatic si es necesario")
        else:
            self.stdout.write("✅ Todas las imágenes parecen estar configuradas correctamente")
