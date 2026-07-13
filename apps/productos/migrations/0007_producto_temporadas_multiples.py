from django.db import migrations, models


def copy_season_to_list(apps, schema_editor):
    Producto = apps.get_model('productos', 'Producto')
    for producto in Producto.objects.all().iterator():
        value = producto.temporada
        producto.temporadas_json = [value] if value else []
        producto.save(update_fields=['temporadas_json'])


def copy_list_to_season(apps, schema_editor):
    Producto = apps.get_model('productos', 'Producto')
    for producto in Producto.objects.all().iterator():
        values = producto.temporadas_json or []
        producto.temporada = values[0] if values else ''
        producto.save(update_fields=['temporada'])


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0006_merge_0002_0005'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='temporadas_json',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(copy_season_to_list, copy_list_to_season),
        migrations.RemoveField(
            model_name='producto',
            name='temporada',
        ),
        migrations.RenameField(
            model_name='producto',
            old_name='temporadas_json',
            new_name='temporada',
        ),
    ]
