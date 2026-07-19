from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0002_perfilusuario_email_verificado'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilusuario',
            name='bloqueado_hasta',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='intentos_login_fallidos',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
