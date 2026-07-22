from django.core.management.base import BaseCommand
from apps.productos.models import Producto
from decimal import Decimal

class Command(BaseCommand):
    help = 'Crear productos de ejemplo para la perfumería (solo si no hay productos)'

    def handle(self, *args, **options):
        # Verificar si ya hay productos
        productos_existentes = Producto.objects.count()
        
        if productos_existentes > 0:
            self.stdout.write(f"📋 Ya existen {productos_existentes} productos en la base de datos.")
            self.stdout.write("🚫 No se crearán productos de ejemplo para proteger los datos existentes.")
            self.stdout.write("=" * 50)
            return
        
        self.stdout.write("🌸 No hay productos en la base de datos. Creando productos de ejemplo...")
        
        # Productos de ejemplo
        productos_data = [
            {
                'nombre': 'Darcy Bloom',
                'marca': 'D.A.R.C.Y.',
                'descripcion': 'Fragancia floral con notas de rosa y jazmín',
                'precio': Decimal('89.99'),
                'tipo': 'eau_de_parfum',
                'tamano_ml': 100,
                'stock': 50,
                'disponible': True,
                'temporada': ['verano', 'dia'],
            },
            {
                'nombre': 'Noche Misteriosa',
                'marca': 'D.A.R.C.Y.',
                'descripcion': 'Aroma intenso con notas de vainilla y ámbar',
                'precio': Decimal('94.99'),
                'tipo': 'eau_de_parfum',
                'tamano_ml': 100,
                'stock': 30,
                'disponible': True,
                'temporada': ['invierno', 'noche'],
            },
            {
                'nombre': 'Urban Spirit',
                'marca': 'D.A.R.C.Y.',
                'descripcion': 'Fragancia moderna con notas cítricas y madera',
                'precio': Decimal('79.99'),
                'tipo': 'eau_de_toilette',
                'tamano_ml': 100,
                'stock': 45,
                'disponible': True,
                'temporada': ['dia'],
            },
            {
                'nombre': 'Power Elite',
                'marca': 'D.A.R.C.Y.',
                'descripcion': 'Aroma poderoso con especias y cuero',
                'precio': Decimal('99.99'),
                'tipo': 'eau_de_parfum',
                'tamano_ml': 100,
                'stock': 25,
                'disponible': True,
                'temporada': ['otono', 'noche'],
            },
            {
                'nombre': 'Free Soul',
                'marca': 'D.A.R.C.Y.',
                'descripcion': 'Fragancia equilibrada para cualquier género',
                'precio': Decimal('84.99'),
                'tipo': 'eau_de_toilette',
                'tamano_ml': 100,
                'stock': 40,
                'disponible': True,
                'temporada': ['dia'],
            },
            {
                'nombre': 'Crystal Waters',
                'marca': 'D.A.R.C.Y.',
                'descripcion': 'Aroma fresco con notas acuáticas y musgo',
                'precio': Decimal('74.99'),
                'tipo': 'eau_de_cologne',
                'tamano_ml': 100,
                'stock': 35,
                'disponible': True,
                'temporada': ['verano', 'dia'],
            },
            {
                'nombre': 'Silk Body Lotion',
                'marca': 'D.A.R.C.Y.',
                'descripcion': 'Loción corporal hidratante con fragancia suave',
                'precio': Decimal('34.99'),
                'tipo': 'body_spray',
                'tamano_ml': 200,
                'stock': 60,
                'disponible': True,
                'temporada': ['dia'],
            },
            {
                'nombre': 'Golden Shower Gel',
                'marca': 'D.A.R.C.Y.',
                'descripcion': 'Gel de ducha con aroma exótico',
                'precio': Decimal('29.99'),
                'tipo': 'body_spray',
                'tamano_ml': 250,
                'stock': 80,
                'disponible': True,
                'temporada': ['verano'],
            },
        ]
        
        for prod_data in productos_data:
            producto, created = Producto.objects.get_or_create(
                nombre=prod_data['nombre'],
                defaults=prod_data
            )
            
            if created:
                self.stdout.write(f"✅ Producto creado: {producto.nombre} - ${producto.precio:,.1f}")
            else:
                self.stdout.write(f"📋 Producto ya existe: {producto.nombre}")
        
        self.stdout.write("=" * 50)
        self.stdout.write(f"🌸 Total productos: {Producto.objects.count()}")
        self.stdout.write("✅ Productos de ejemplo creados exitosamente!")
        self.stdout.write("=" * 50)
