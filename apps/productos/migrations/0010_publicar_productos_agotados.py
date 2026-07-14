from django.db import migrations


def publicar_productos_desactivados_por_stock(apps, schema_editor):
    Producto = apps.get_model('productos', 'Producto')
    Producto.objects.filter(stock=0, disponible=False).update(disponible=True)


class Migration(migrations.Migration):
    dependencies = [
        ('productos', '0009_producto_campos_opcionales'),
    ]

    operations = [
        migrations.RunPython(
            publicar_productos_desactivados_por_stock,
            migrations.RunPython.noop,
        ),
    ]
