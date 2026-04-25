from django.core.management.base import BaseCommand
from apps.productos.models import Producto
from decimal import Decimal

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
        existentes = 0
        
        for prod_data in productos_originales:
            producto, created = Producto.objects.get_or_create(
                nombre=prod_data['nombre'],
                marca=prod_data['marca'],
                defaults=prod_data
            )
            
            if created:
                self.stdout.write(f"✅ Producto creado: {producto.nombre} ({producto.marca}) - ${producto.precio}")
                creados += 1
            else:
                self.stdout.write(f"📋 Producto ya existe: {producto.nombre} ({producto.marca})")
                existentes += 1
        
        self.stdout.write("=" * 60)
        self.stdout.write(f"🌸 Resumen:")
        self.stdout.write(f"✅ Creados: {creados} productos")
        self.stdout.write(f"📋 Ya existían: {existentes} productos")
        self.stdout.write(f"🛍️ Total productos en BD: {Producto.objects.count()}")
        self.stdout.write("🎉 ¡Tus productos originales están listos!")
        self.stdout.write("=" * 60)
