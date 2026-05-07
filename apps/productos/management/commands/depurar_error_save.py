from django.core.management.base import BaseCommand
from apps.productos.models import Producto
import traceback
import sys

class Command(BaseCommand):
    help = 'Depurar error 500 al guardar productos'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Depurando error 500 al guardar productos...")
        
        # Probar guardar un producto con imagen
        try:
            self.stdout.write("📋 Creando producto de prueba...")
            
            # Buscar un producto existente
            producto = Producto.objects.first()
            if producto:
                self.stdout.write(f"📋 Producto encontrado: {producto.nombre}")
                
                # Intentar guardar sin cambios
                self.stdout.write("💾 Intentando guardar sin cambios...")
                try:
                    producto.save()
                    self.stdout.write("✅ Guardado sin cambios: EXITOSO")
                except Exception as e:
                    self.stdout.write(f"❌ Error guardando sin cambios: {str(e)}")
                    self.stdout.write("📊 Traceback:")
                    self.stdout.write(traceback.format_exc())
                
                # Intentar guardar con imagen base64
                if not producto.imagen_base64:
                    self.stdout.write("🖼️ Intentando guardar con imagen base64...")
                    try:
                        # Crear imagen base64 de prueba
                        import base64
                        imagen_prueba = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                        producto.imagen_base64 = imagen_prueba
                        producto.imagen_nombre = "test.jpg"
                        producto.save()
                        self.stdout.write("✅ Guardado con imagen base64: EXITOSO")
                    except Exception as e:
                        self.stdout.write(f"❌ Error guardando con imagen base64: {str(e)}")
                        self.stdout.write("📊 Traceback:")
                        self.stdout.write(traceback.format_exc())
                
            else:
                self.stdout.write("❌ No se encontró productos para probar")
                
        except Exception as e:
            self.stdout.write(f"❌ Error general: {str(e)}")
            self.stdout.write("📊 Traceback completo:")
            self.stdout.write(traceback.format_exc())
        
        # Verificar configuración del modelo
        self.stdout.write("=" * 60)
        self.stdout.write("⚙️  CONFIGURACIÓN DEL MODELO:")
        
        # Verificar campos del modelo
        campos = [field.name for field in Producto._meta.fields]
        self.stdout.write(f"   📋 Campos: {campos}")
        
        # Verificar si imagen_base64 existe en la BD
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM productos_producto WHERE imagen_base64 IS NOT NULL")
                count = cursor.fetchone()[0]
                self.stdout.write(f"   🖼️ Productos con imagen_base64: {count}")
                
                cursor.execute("PRAGMA table_info(productos_producto)")
                columns = cursor.fetchall()
                self.stdout.write("   📊 Columnas en la tabla:")
                for column in columns:
                    self.stdout.write(f"      - {column}")
        except Exception as e:
            self.stdout.write(f"   ❌ Error verificando tabla: {str(e)}")
        
        self.stdout.write("=" * 60)
        self.stdout.write("🎉 DEPURACIÓN COMPLETADA")
        self.stdout.write("📋 Revisa los logs para identificar el problema exacto")
        self.stdout.write("🔧 Posibles soluciones:")
        self.stdout.write("   1. Revisar método save() para bucles infinitos")
        self.stdout.write("   2. Verificar manejo de archivos grandes")
        self.stdout.write("   3. Revisar permisos de escritura")
        self.stdout.write("   4. Verificar límites de memoria en producción")
