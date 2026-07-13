from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0008_quitar_fondo_imagenes_existentes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='producto',
            name='nombre',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AlterField(
            model_name='producto',
            name='marca',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='producto',
            name='descripcion',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='producto',
            name='precio',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='producto',
            name='tipo',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='producto',
            name='tamano_ml',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='producto',
            name='stock',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]
