from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.conf import settings
from apps.productos.models import Producto
import os
import requests
from django.core.files.base import ContentFile

class Command(BaseCommand):
    help = 'Depurar imagen específica productos/2500263.png'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Depurando imagen específica productos/2500263.png...")
        
        # Buscar producto con esa imagen
        productos_con_imagen = Producto.objects.filter(imagen__icontains='2500263')
        
        if productos_con_imagen.exists():
            for producto in productos_con_imagen:
                self.stdout.write(f"📋 Producto encontrado: {producto.nombre}")
                self.stdout.write(f"🖼️ Imagen en BD: {producto.imagen.name}")
                self.stdout.write(f"🔗 URL generada: {producto.imagen.url}")
                
                # Verificar si el archivo existe
                if default_storage.exists(producto.imagen.name):
                    self.stdout.write(f"✅ Archivo EXISTE en storage")
                    
                    # Verificar tamaño y tipo
                    try:
                        size = default_storage.size(producto.imagen.name)
                        self.stdout.write(f"📊 Tamaño: {size} bytes")
                    except Exception as e:
                        self.stdout.write(f"❌ Error obteniendo tamaño: {e}")
                else:
                    self.stdout.write(f"❌ Archivo NO EXISTE en storage")
                    
                    # Descargar y guardar la imagen
                    try:
                        self.stdout.write("📸 Descargando imagen de reemplazo...")
                        imagen_url = 'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400&h=400&fit=crop'
                        response = requests.get(imagen_url)
                        
                        if response.status_code == 200:
                            # Guardar con el mismo nombre
                            producto.imagen.save('productos/2500263.png', ContentFile(response.content), save=True)
                            self.stdout.write("✅ Imagen reemplazada exitosamente")
                        else:
                            self.stdout.write(f"❌ Error descargando imagen: {response.status_code}")
                    except Exception as e:
                        self.stdout.write(f"❌ Error procesando imagen: {str(e)}")
        else:
            self.stdout.write("❌ No se encontró producto con imagen productos/2500263.png")
            
            # Mostrar todas las imágenes de productos
            self.stdout.write("📋 Todas las imágenes de productos:")
            todos_productos = Producto.objects.exclude(imagen__isnull=True).exclude(imagen='')
            for producto in todos_productos:
                self.stdout.write(f"   📄 {producto.nombre}: {producto.imagen.name}")
                existe = default_storage.exists(producto.imagen.name)
                self.stdout.write(f"      {'✅ EXISTE' if existe else '❌ NO EXISTE'}")
        
        # Verificar configuración de rutas
        self.stdout.write("=" * 60)
        self.stdout.write("⚙️  CONFIGURACIÓN DE RUTAS:")
        self.stdout.write(f"   MEDIA_URL: {settings.MEDIA_URL}")
        self.stdout.write(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
        self.stdout.write(f"   Storage: {default_storage.__class__.__name__}")
        
        # Verificar directorio productos
        productos_dir = os.path.join(settings.MEDIA_ROOT, 'productos')
        if os.path.exists(productos_dir):
            self.stdout.write(f"📁 Directorio productos: ✅ EXISTE")
            try:
                archivos = os.listdir(productos_dir)
                self.stdout.write(f"   📄 Archivos encontrados: {len(archivos)}")
                for archivo in archivos:
                    if archivo.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                        ruta_completa = os.path.join(productos_dir, archivo)
                        tamaño = os.path.getsize(ruta_completa)
                        self.stdout.write(f"      📄 {archivo} ({tamaño} bytes)")
            except Exception as e:
                self.stdout.write(f"   Error listando archivos: {e}")
        else:
            self.stdout.write(f"📁 Directorio productos: ❌ NO EXISTE")
            # Crearlo
            try:
                os.makedirs(productos_dir, exist_ok=True)
                self.stdout.write(f"📁 Directorio productos: ✅ CREADO")
            except Exception as e:
                self.stdout.write(f"❌ Error creando directorio: {e}")
        
        # Probar URL directa
        self.stdout.write("=" * 60)
        self.stdout.write("🌐 PRUEBA DE URL DIRECTA:")
        url_prueba = f"{settings.MEDIA_URL}productos/2500263.png"
        self.stdout.write(f"   URL: {url_prueba}")
        
        # Verificar si la URL es accesible
        if settings.MEDIA_URL.startswith('/'):
            url_completa = url_prueba
        else:
            url_completa = settings.MEDIA_URL + url_prueba
        
        self.stdout.write(f"   URL completa: {url_completa}")
        
        self.stdout.write("=" * 60)
        self.stdout.write("🎉 DEPURACIÓN COMPLETADA")
