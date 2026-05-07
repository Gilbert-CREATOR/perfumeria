from django.core.management.base import BaseCommand
from apps.productos.models import Producto
import traceback

class Command(BaseCommand):
    help = 'Probar guardado simple de productos'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Probando guardado simple de productos...")
        
        try:
            # Buscar un producto existente
            producto = Producto.objects.first()
            if producto:
                self.stdout.write(f"📋 Producto encontrado: {producto.nombre}")
                self.stdout.write(f"🖼️ Imagen: {producto.imagen}")
                self.stdout.write(f"📊 Stock: {producto.stock}")
                
                # Intentar guardar
                self.stdout.write("💾 Intentando guardar...")
                producto.save()
                self.stdout.write("✅ Guardado simple: EXITOSO")
                
            else:
                self.stdout.write("❌ No se encontró productos para probar")
                
        except Exception as e:
            self.stdout.write(f"❌ Error: {str(e)}")
            self.stdout.write("📊 Traceback:")
            self.stdout.write(traceback.format_exc())
        
        self.stdout.write("=" * 60)
        self.stdout.write("🎉 PRUEBA COMPLETADA")
        self.stdout.write("📋 Si no hay errores, el admin debería funcionar")
        self.stdout.write("🔧 Si hay errores, revisa el traceback arriba")
