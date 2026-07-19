from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_disenocorreo'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracionsitio',
            name='mostrar_animacion_entrada',
            field=models.BooleanField(
                default=True,
                help_text='Se muestra una vez por sesión y usa automáticamente el nombre de la tienda.',
                verbose_name='Mostrar animación del nombre al entrar',
            ),
        ),
    ]
