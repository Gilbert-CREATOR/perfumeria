from django.core.management.base import BaseCommand
from apps.productos.models import Producto
from decimal import Decimal
from django.core.files import File
import os

class Command(BaseCommand):
    help = 'Crear los 3 productos originales del usuario'

    def handle(self, *args, **options):
        self.stdout.write("🌸 Creando los 3 productos originales del usuario...")
        
        # Verificar si ya hay productos
        productos_existentes = Producto.objects.count()
        
        if productos_existentes > 0:
            self.stdout.write(f"📋 Ya existen {productos_existentes} productos en la base de datos.")
            self.stdout.write("🚫 No se crearán productos de ejemplo para proteger los datos existentes.")
            self.stdout.write("=" * 50)
            return
        
        self.stdout.write("🌸 No hay productos en la base de datos. Creando productos de ejemplo...")
        
        # Productos originales del usuario
        productos_originales = [
            {
                'nombre': 'Invictus',
                'marca': 'Paco Rabanne',
                'descripcion': 'Fragancia masculina intensa con notas de madera y vainilla',
                'precio': Decimal('7500.00'),
                'tipo': 'eau_de_parfum',
                'tamano_ml': 100,
                'stock': 30,
                'disponible': True,
                'temporada': 'day',
                'imagen': 'perfumes/ejemplo.jpg',
            },
            {
                'nombre': 'Versace Eros',
                'marca': 'Versace',
                'descripcion': 'Aroma poderoso y seductor con notas de menta y manzana verde',
                'precio': Decimal('5500.00'),
                'tipo': 'eau_de_parfum',
                'tamano_ml': 100,
                'stock': 25,
                'disponible': True,
                'temporada': 'night',
                'imagen': 'perfumes/ejemplo.jpg',
            },
            {
                'nombre': 'Stallion 53',
                'marca': 'Emper',
                'descripcion': 'Fragancia elegante y sofisticada con notas cítricas y especias',
                'precio': Decimal('3200.00'),
                'tipo': 'eau_de_toilette',
                'tamano_ml': 100,
                'stock': 20,
                'disponible': True,
                'temporada': 'special',
                'imagen': 'perfumes/ejemplo.jpg',
            },
        ]
        
        creados = 0
        existentes = 0
        
        for prod_data in productos_originales:
            # Extraer la ruta de la imagen
            imagen_path = prod_data.pop('imagen', None)
            
            producto, created = Producto.objects.get_or_create(
                nombre=prod_data['nombre'],
                marca=prod_data['marca'],
                defaults=prod_data
            )
            
            if created:
                # Asignar imagen si existe
                if imagen_path and os.path.exists(os.path.join('media', imagen_path)):
                    with open(os.path.join('media', imagen_path), 'rb') as f:
                        producto.imagen.save(imagen_path, File(f), save=True)
                    self.stdout.write(f"✅ Producto creado con imagen: {producto.nombre} - ${producto.precio}")
                else:
                    self.stdout.write(f"✅ Producto creado sin imagen: {producto.nombre} - ${producto.precio}")
                creados += 1
            else:
                self.stdout.write(f"📋 Producto ya existe: {producto.nombre}")
                existentes += 1
        
        self.stdout.write("=" * 60)
        self.stdout.write(f"🌸 Resumen:")
        self.stdout.write(f"✅ Creados: {creados} productos")
        self.stdout.write(f"📋 Ya existían: {existentes} productos")
        self.stdout.write(f"🛍️ Total productos en BD: {Producto.objects.count()}")
        self.stdout.write("🎉 ¡Tus productos originales están listos!")
        self.stdout.write("=" * 60)
