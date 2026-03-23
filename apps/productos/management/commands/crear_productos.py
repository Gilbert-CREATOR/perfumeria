from django.core.management.base import BaseCommand
from apps.productos.models import Producto, Categoria
from decimal import Decimal

class Command(BaseCommand):
    help = 'Crear productos de ejemplo para la perfumería'

    def handle(self, *args, **options):
        self.stdout.write("🌸 Creando productos para Perfumería D.A.R.C.Y.")
        
        # Crear categorías
        categorias_data = [
            {'nombre': 'Perfumes Femininos', 'descripcion': 'Fragancias elegantes para mujeres'},
            {'nombre': 'Perfumes Masculinos', 'descripcion': 'Aromas masculinos modernos'},
            {'nombre': 'Perfumes Unisex', 'descripcion': 'Fragancias versátiles para todos'},
            {'nombre': 'Cuerpo y Baño', 'descripcion': 'Productos para el cuidado corporal'},
        ]
        
        for cat_data in categorias_data:
            categoria, created = Categoria.objects.get_or_create(
                nombre=cat_data['nombre'],
                defaults={'descripcion': cat_data['descripcion']}
            )
            if created:
                self.stdout.write(f"✅ Categoría creada: {categoria.nombre}")
        
        # Productos de ejemplo
        productos_data = [
            {
                'nombre': 'Darcy Bloom',
                'descripcion': 'Fragancia floral con notas de rosa y jazmín',
                'precio': Decimal('89.99'),
                'categoria': 'Perfumes Femininos',
                'stock': 50,
                'imagen': 'productos/darcy_bloom.jpg',
                'popularidad': 95
            },
            {
                'nombre': 'Noche Misteriosa',
                'descripcion': 'Aroma intenso con notas de vainilla y ámbar',
                'precio': Decimal('94.99'),
                'categoria': 'Perfumes Femininos',
                'stock': 30,
                'imagen': 'productos/noche_misteriosa.jpg',
                'popularidad': 88
            },
            {
                'nombre': 'Urban Spirit',
                'descripcion': 'Fragancia moderna con notas cítricas y madera',
                'precio': Decimal('79.99'),
                'categoria': 'Perfumes Masculinos',
                'stock': 45,
                'imagen': 'productos/urban_spirit.jpg',
                'popularidad': 92
            },
            {
                'nombre': 'Power Elite',
                'descripcion': 'Aroma poderoso con especias y cuero',
                'precio': Decimal('99.99'),
                'categoria': 'Perfumes Masculinos',
                'stock': 25,
                'imagen': 'productos/power_elite.jpg',
                'popularidad': 85
            },
            {
                'nombre': 'Free Soul',
                'descripcion': 'Fragancia equilibrada para cualquier género',
                'precio': Decimal('84.99'),
                'categoria': 'Perfumes Unisex',
                'stock': 40,
                'imagen': 'productos/free_soul.jpg',
                'popularidad': 90
            },
            {
                'nombre': 'Crystal Waters',
                'descripcion': 'Aroma fresco con notas acuáticas y musgo',
                'precio': Decimal('74.99'),
                'categoria': 'Perfumes Unisex',
                'stock': 35,
                'imagen': 'productos/crystal_waters.jpg',
                'popularidad': 87
            },
            {
                'nombre': 'Silk Body Lotion',
                'descripcion': 'Loción corporal hidratante con fragancia suave',
                'precio': Decimal('34.99'),
                'categoria': 'Cuerpo y Baño',
                'stock': 60,
                'imagen': 'productos/silk_lotion.jpg',
                'popularidad': 78
            },
            {
                'nombre': 'Golden Shower Gel',
                'descripcion': 'Gel de ducha con aroma exótico',
                'precio': Decimal('29.99'),
                'categoria': 'Cuerpo y Baño',
                'stock': 80,
                'imagen': 'productos/golden_shower.jpg',
                'popularidad': 82
            },
        ]
        
        for prod_data in productos_data:
            categoria = Categoria.objects.get(nombre=prod_data['categoria'])
            
            producto, created = Producto.objects.get_or_create(
                nombre=prod_data['nombre'],
                defaults={
                    'descripcion': prod_data['descripcion'],
                    'precio': prod_data['precio'],
                    'categoria': categoria,
                    'stock': prod_data['stock'],
                    'imagen': prod_data['imagen'],
                    'popularidad': prod_data['popularidad'],
                    'activo': True
                }
            )
            
            if created:
                self.stdout.write(f"✅ Producto creado: {producto.nombre} - ${producto.precio}")
            else:
                self.stdout.write(f"📋 Producto ya existe: {producto.nombre}")
        
        self.stdout.write("=" * 50)
        self.stdout.write(f"🌸 Total productos: {Producto.objects.count()}")
        self.stdout.write(f"📂 Total categorías: {Categoria.objects.count()}")
        self.stdout.write("✅ Productos de ejemplo creados exitosamente!")
        self.stdout.write("=" * 50)
