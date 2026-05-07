from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.productos.models import Producto
import requests
from io import BytesIO

class Command(BaseCommand):
    help = 'Crear imágenes de prueba para productos'

    def handle(self, *args, **options):
        self.stdout.write("🖼️ Creando imágenes de prueba para productos...")
        
        # URLs de imágenes de perfumes placeholder
        imagenes_prueba = [
            'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400&h=400&fit=crop',  # Perfume 1
            'https://images.unsplash.com/photo-1590736969955-71cc94901144?w=400&h=400&fit=crop',  # Perfume 2
            'https://images.unsplash.com/photo-1541643600964-78399582799c?w=400&h=400&fit=crop',  # Perfume 3
            'https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=400&h=400&fit=crop',  # Perfume 4
            'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400&h=400&fit=crop',  # Perfume 5
        ]
        
        productos_sin_imagen = Producto.objects.filter(imagen='')
        total_productos = productos_sin_imagen.count()
        
        if total_productos == 0:
            self.stdout.write("✅ Todos los productos ya tienen imágenes")
            return
        
        self.stdout.write(f"📊 Encontrados {total_productos} productos sin imagen")
        
        for i, producto in enumerate(productos_sin_imagen[:5]):  # Limitar a 5 productos
            try:
                # Descargar imagen
                response = requests.get(imagenes_prueba[i % len(imagenes_prueba)])
                if response.status_code == 200:
                    # Guardar imagen
                    imagen_nombre = f"perfume_{producto.nombre.replace(' ', '_').lower()}.jpg"
                    producto.imagen.save(imagen_nombre, ContentFile(response.content), save=True)
                    self.stdout.write(f"✅ Imagen agregada a: {producto.nombre}")
                else:
                    self.stdout.write(f"❌ Error descargando imagen para: {producto.nombre}")
            except Exception as e:
                self.stdout.write(f"❌ Error procesando {producto.nombre}: {str(e)}")
        
        self.stdout.write("=" * 50)
        self.stdout.write("🎉 Imágenes de prueba creadas!")
        self.stdout.write("📍 Las imágenes ahora deberían verse en el catálogo")
        self.stdout.write("🌐 URL: https://perfumeria-darcy.onrender.com/catalogo/")
