from django.db import migrations, models


def eliminar_resenas_duplicadas(apps, schema_editor):
    Resena = apps.get_model('productos', 'Resena')
    vistos = set()
    for resena in Resena.objects.order_by('-creado', '-id').iterator():
        clave = (resena.usuario_id, resena.producto_id)
        if clave in vistos:
            resena.delete()
        else:
            vistos.add(clave)


class Migration(migrations.Migration):
    dependencies = [
        ('productos', '0012_alertastock'),
    ]

    operations = [
        migrations.RunPython(eliminar_resenas_duplicadas, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='resena',
            constraint=models.UniqueConstraint(
                fields=('usuario', 'producto'),
                name='resena_unica_por_usuario_producto',
            ),
        ),
    ]
