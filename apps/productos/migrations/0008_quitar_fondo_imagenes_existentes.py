import base64
import binascii

from django.core.files.base import ContentFile
from django.db import migrations


def remove_existing_backgrounds(apps, schema_editor):
    from apps.productos.image_processing import remove_uniform_background

    Producto = apps.get_model('productos', 'Producto')
    productos = Producto.objects.exclude(imagen_base64__isnull=True).exclude(imagen_base64='')

    for producto in productos.iterator():
        try:
            current_image = ContentFile(
                base64.b64decode(producto.imagen_base64),
                name=producto.imagen_nombre or f'producto_{producto.pk}.png',
            )
            processed_image = remove_uniform_background(current_image)
            processed_image.seek(0)
            producto.imagen_base64 = base64.b64encode(processed_image.read()).decode('ascii')
            producto.imagen_nombre = processed_image.name
            producto.save(update_fields=['imagen_base64', 'imagen_nombre'])
        except (OSError, ValueError, TypeError, binascii.Error):
            # Una imagen antigua dañada no debe impedir el despliegue completo.
            continue


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0007_producto_temporadas_multiples'),
    ]

    operations = [
        migrations.RunPython(remove_existing_backgrounds, migrations.RunPython.noop),
    ]
