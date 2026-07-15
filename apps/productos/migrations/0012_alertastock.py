from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('productos', '0011_temporadas_con_porcentajes'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlertaStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creada', models.DateTimeField(auto_now_add=True)),
                ('enviada', models.DateTimeField(blank=True, null=True)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alertas_stock', to='productos.producto')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alertas_stock', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('usuario', 'producto'), name='alerta_stock_unica_por_usuario_producto')],
            },
        ),
    ]
