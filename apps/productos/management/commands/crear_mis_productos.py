from django.core.management.base import BaseCommand
from apps.productos.models import Producto
from decimal import Decimal
from django.core.files import File
import os

class Command(BaseCommand):
    help = 'Crear los 3 productos originales del usuario'

    def handle(self, *args, **options):
        self.stdout.write("🌸 Creando los 3 productos originales del usuario...")
        
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
            },
        ]
        
        creados = 0
        actualizados = 0
        
        for prod_data in productos_originales:
            nombre = prod_data['nombre']
            marca = prod_data['marca']
            
            # Buscar si el producto ya existe
            producto = None
            try:
                producto = Producto.objects.get(nombre=nombre, marca=marca)
                self.stdout.write(f"📋 Producto ya existe: {producto.nombre}")
                actualizados += 1
            except Producto.DoesNotExist:
                # Crear nuevo producto
                producto = Producto.objects.create(**prod_data)
                self.stdout.write(f"✅ Producto creado: {producto.nombre} - ${producto.precio}")
                creados += 1
            
            # Asignar imagen si existe
            imagen_path = 'perfumes/ejemplo.jpg'
            ruta_completa = os.path.join('media', imagen_path)
            
            if os.path.exists(ruta_completa):
                try:
                    with open(ruta_completa, 'rb') as f:
                        producto.imagen.save(imagen_path, File(f), save=True)
                    self.stdout.write(f"🖼️  Imagen asignada: {producto.nombre}")
                except Exception as e:
                    self.stdout.write(f"⚠️  Error al asignar imagen a {producto.nombre}: {str(e)}")
            else:
                self.stdout.write(f"⚠️  Imagen no encontrada: {ruta_completa}")
        
        self.stdout.write("=" * 60)
        self.stdout.write(f"🌸 Resumen:")
        self.stdout.write(f"✅ Creados: {creados} productos")
        self.stdout.write(f"📋 Actualizados: {actualizados} productos")
        self.stdout.write(f"🛍️ Total productos en BD: {Producto.objects.count()}")
        self.stdout.write("🎉 ¡Tus productos originales están listos!")
        self.stdout.write("=" * 60)
