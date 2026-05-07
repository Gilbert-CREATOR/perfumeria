from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.conf import settings
from apps.productos.models import Producto
import os
from django.templatetags.static import static

class Command(BaseCommand):
    help = 'Forzar que las imágenes sean visibles en el catálogo'

    def handle(self, *args, **options):
        self.stdout.write("🖼️ Forzando visibilidad de imágenes...")
        
        # Verificar configuración actual
        self.stdout.write("⚙️  Configuración actual:")
        self.stdout.write(f"   MEDIA_URL: {settings.MEDIA_URL}")
        self.stdout.write(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
        self.stdout.write(f"   Storage: {default_storage.__class__.__name__}")
        
        # Crear directorio media si no existe
        media_root = settings.MEDIA_ROOT
        if not os.path.exists(media_root):
            os.makedirs(media_root, exist_ok=True)
            self.stdout.write(f"📁 Creado directorio: {media_root}")
        
        # Procesar todos los productos
        productos = Producto.objects.all()
        total_productos = productos.count()
        productos_actualizados = 0
        
        for producto in productos:
            if producto.imagen:
                # Verificar si el archivo existe
                if default_storage.exists(producto.imagen.name):
                    self.stdout.write(f"✅ {producto.nombre}: {producto.imagen.name} - EXISTE")
                    
                    # Verificar URL generada
                    url_generada = producto.imagen.url
                    self.stdout.write(f"   URL: {url_generada}")
                    
                    # Probar URL completa
                    if settings.MEDIA_URL.startswith('/'):
                        url_completa = url_generada
                    else:
                        url_completa = settings.MEDIA_URL + url_generada
                    
                    self.stdout.write(f"   URL completa: {url_completa}")
                    
                else:
                    self.stdout.write(f"❌ {producto.nombre}: {producto.imagen.name} - NO EXISTE")
                    # Eliminar referencia rota
                    producto.imagen = None
                    producto.save()
                    productos_actualizados += 1
            else:
                self.stdout.write(f"⚠️  {producto.nombre}: SIN IMAGEN")
        
        # Crear imágenes de prueba para productos sin imagen
        productos_sin_imagen = Producto.objects.filter(imagen__isnull=True) | Producto.objects.filter(imagen='')
        
        if productos_sin_imagen.exists():
            self.stdout.write(f"🖼️ Creando imágenes para {productos_sin_imagen.count()} productos sin imagen...")
            
            # URLs de imágenes de prueba
            imagenes_prueba = [
                'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1590736969955-71cc94901144?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1541643600964-78399582799c?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=400&h=400&fit=crop',
                'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400&h=400&fit=crop',
            ]
            
            import requests
            from django.core.files.base import ContentFile
            
            for i, producto in enumerate(productos_sin_imagen[:5]):
                try:
                    # Descargar imagen
                    response = requests.get(imagenes_prueba[i % len(imagenes_prueba)])
                    if response.status_code == 200:
                        # Guardar con nombre específico
                        nombre_archivo = f"productos/perfume_{producto.nombre.replace(' ', '_').lower()}.jpg"
                        producto.imagen.save(nombre_archivo, ContentFile(response.content), save=True)
                        productos_actualizados += 1
                        self.stdout.write(f"✅ Imagen creada: {producto.nombre}")
                    else:
                        self.stdout.write(f"❌ Error descargando imagen para: {producto.nombre}")
                except Exception as e:
                    self.stdout.write(f"❌ Error procesando {producto.nombre}: {str(e)}")
        
        # Verificar directorio de productos
        productos_dir = os.path.join(media_root, 'productos')
        if os.path.exists(productos_dir):
            self.stdout.write(f"📁 Archivos en {productos_dir}:")
            try:
                for file in os.listdir(productos_dir):
                    if file.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                        self.stdout.write(f"   📄 {file}")
            except Exception as e:
                self.stdout.write(f"   Error listando archivos: {e}")
        else:
            self.stdout.write(f"📁 Directorio productos no existe: {productos_dir}")
        
        self.stdout.write("=" * 60)
        self.stdout.write("🎉 PROCESO COMPLETADO:")
        self.stdout.write(f"   Productos procesados: {total_productos}")
        self.stdout.write(f"   Productos actualizados: {productos_actualizados}")
        self.stdout.write("📍 Las imágenes ahora deberían ser visibles en:")
        self.stdout.write("   🌐 https://perfumeria-darcy.onrender.com/catalogo/")
        self.stdout.write("   🖼️ https://perfumeria-darcy.onrender.com/media/")
