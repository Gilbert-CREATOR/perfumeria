# Generated manually for the newsletter subscription feature.
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name='SuscriptorNewsletter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('activo', models.BooleanField(default=True)),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('fecha_suscripcion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='suscripciones_newsletter', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'suscriptor del newsletter',
                'verbose_name_plural': 'suscriptores del newsletter',
                'ordering': ('-fecha_suscripcion',),
            },
        ),
    ]
