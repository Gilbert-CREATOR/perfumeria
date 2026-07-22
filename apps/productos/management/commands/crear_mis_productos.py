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
                'temporada': ['dia'],
                'temporada_porcentajes': {'dia': 100},
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
                'temporada': ['noche'],
                'temporada_porcentajes': {'noche': 100},
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
                'temporada': ['otono'],
                'temporada_porcentajes': {'otono': 100},
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
                self.stdout.write(f"✅ Producto creado: {producto.nombre} - ${producto.precio:,.1f}")
                creados += 1
        
        self.stdout.write("=" * 60)
        self.stdout.write(f"🌸 Resumen:")
        self.stdout.write(f"✅ Creados: {creados} productos")
        self.stdout.write(f"📋 Actualizados: {actualizados} productos")
        self.stdout.write(f"🛍️ Total productos en BD: {Producto.objects.count()}")
        self.stdout.write("🎉 ¡Tus productos originales están listos!")
        self.stdout.write("📝 NOTA: Agrega imágenes desde el panel admin")
        self.stdout.write("=" * 60)
