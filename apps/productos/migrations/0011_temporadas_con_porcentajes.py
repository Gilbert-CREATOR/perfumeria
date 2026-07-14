from django.db import migrations, models


MAPEO_TEMPORADAS = {
    'summer': 'verano',
    'verano': 'verano',
    'winter': 'invierno',
    'invierno': 'invierno',
    'spring': 'primavera',
    'primavera': 'primavera',
    'autumn': 'otono',
    'fall': 'otono',
    'otono': 'otono',
    'otoño': 'otono',
    'day': 'dia',
    'dia': 'dia',
    'día': 'dia',
    'night': 'noche',
    'noche': 'noche',
    'special': 'otono',
}


def normalizar_temporadas(apps, schema_editor):
    Producto = apps.get_model('productos', 'Producto')
    orden = ('invierno', 'primavera', 'verano', 'otono', 'dia', 'noche')

    for producto in Producto.objects.all().iterator():
        valores = producto.temporada or []
        if isinstance(valores, str):
            valores = [valores]
        convertidos = {
            MAPEO_TEMPORADAS.get(str(valor).strip().lower())
            for valor in valores
        }
        temporadas = [valor for valor in orden if valor in convertidos]
        producto.temporada = temporadas
        producto.temporada_porcentajes = {valor: 100 for valor in temporadas}
        producto.save(update_fields=['temporada', 'temporada_porcentajes'])


class Migration(migrations.Migration):
    dependencies = [
        ('productos', '0010_publicar_productos_agotados'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='temporada_porcentajes',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.RunPython(normalizar_temporadas, migrations.RunPython.noop),
    ]
