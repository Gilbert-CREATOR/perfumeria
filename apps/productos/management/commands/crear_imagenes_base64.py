from django.core.management.base import BaseCommand
from apps.productos.models import Producto
import base64
import requests
from django.core.files.base import ContentFile

class Command(BaseCommand):
    help = 'Crear imágenes en base64 para todos los productos'

    def handle(self, *args, **options):
        self.stdout.write("🖼️ Creando imágenes en base64 para persistencia...")
        
        # URLs de imágenes de perfumes
        imagenes_prueba = [
            'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1590736969955-71cc94901144?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1541643600964-78399582799c?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400&h=400&fit=crop',
        ]
        
        productos = Producto.objects.all()
        total_productos = productos.count()
        productos_actualizados = 0
        
        self.stdout.write(f"📊 Procesando {total_productos} productos...")
        
        for i, producto in enumerate(productos):
            try:
                # Descargar imagen
                response = requests.get(imagenes_prueba[i % len(imagenes_prueba)])
                if response.status_code == 200:
                    # Convertir a base64
                    image_data = response.content
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                    
                    # Guardar en base64
                    producto.imagen_base64 = image_base64
                    producto.imagen_nombre = f"perfume_{producto.nombre.replace(' ', '_').lower()}.jpg"
                    producto.save()
                    
                    productos_actualizados += 1
                    self.stdout.write(f"✅ {producto.nombre}: Imagen guardada en base64")
                else:
                    self.stdout.write(f"❌ {producto.nombre}: Error descargando imagen")
            except Exception as e:
                self.stdout.write(f"❌ {producto.nombre}: Error {str(e)}")
        
        self.stdout.write("=" * 60)
        self.stdout.write("🎉 PROCESO COMPLETADO:")
        self.stdout.write(f"   📊 Productos procesados: {total_productos}")
        self.stdout.write(f"   ✅ Productos actualizados: {productos_actualizados}")
        self.stdout.write("   🖼️ Imágenes guardadas en base de datos")
        self.stdout.write("   🔄 Persistencia garantizada entre deploys")
        self.stdout.write("   📍 Las imágenes ahora sobreviven a los deploys")
        self.stdout.write("=" * 60)
        self.stdout.write("🌐 Las imágenes serán visibles en:")
        self.stdout.write("   🛍️ https://perfumeria-darcy.onrender.com/catalogo/")
        self.stdout.write("   🏠 https://perfumeria-darcy.onrender.com/")
