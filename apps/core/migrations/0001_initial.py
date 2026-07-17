from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='ConfiguracionSitio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('marca', models.CharField(default='D.A.R.C.Y.', max_length=80)),
                ('titulo_home', models.CharField(default='D.A.R.C.Y.', max_length=120)),
                ('texto_nosotros', models.TextField(blank=True, default='Minimalist design meets exceptional fragrance. We believe in the power of simplicity and the art of perfumery.')),
                ('texto_filosofia', models.TextField(blank=True, default='At D.A.R.C.Y., we believe that less is more. We remove the unnecessary to reveal the true essence of each scent.')),
                ('texto_artesania', models.TextField(blank=True, default='We work with carefully selected ingredients, combining traditional perfumery with modern minimalist design.')),
                ('valor_1_titulo', models.CharField(default='Simplicity', max_length=80)),
                ('valor_1_texto', models.CharField(default='Stripping away the unnecessary to reveal true beauty', max_length=240)),
                ('valor_2_titulo', models.CharField(default='Quality', max_length=80)),
                ('valor_2_texto', models.CharField(default='Only the finest ingredients and craftsmanship', max_length=240)),
                ('valor_3_titulo', models.CharField(default='Innovation', max_length=80)),
                ('valor_3_texto', models.CharField(default='Pushing boundaries while respecting tradition', max_length=240)),
                ('texto_estudio', models.TextField(blank=True, default='Visit our studio to explore the collection and discover your signature scent.')),
                ('direccion_linea_1', models.CharField(default='CLEVENKA 33 DK', max_length=160)),
                ('direccion_linea_2', models.CharField(blank=True, default='Santiago, RD', max_length=160)),
                ('email_contacto', models.EmailField(default='info@darcy.com', max_length=254)),
                ('telefono_contacto', models.CharField(default='+11233455678', max_length=40)),
                ('whatsapp', models.CharField(blank=True, max_length=40)),
                ('horario_semana', models.CharField(default='9:00 AM - 7:00 PM', max_length=100)),
                ('horario_sabado', models.CharField(default='9:00 AM - 5:00 PM', max_length=100)),
                ('horario_domingo', models.CharField(default='Cerrado', max_length=100)),
                ('instagram_url', models.URLField(blank=True, default='https://www.instagram.com/')),
                ('facebook_url', models.URLField(blank=True, default='https://www.facebook.com/')),
                ('twitter_url', models.URLField(blank=True, default='https://x.com/')),
                ('mapa_embed_url', models.URLField(blank=True, max_length=1000)),
                ('texto_politica_envios', models.TextField(blank=True)),
                ('texto_terminos', models.TextField(blank=True)),
                ('mostrar_newsletter', models.BooleanField(default=True)),
                ('actualizado', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'configuración del sitio', 'verbose_name_plural': 'configuración del sitio'},
        ),
        migrations.CreateModel(
            name='PreguntaFrecuente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pregunta', models.CharField(max_length=240)),
                ('respuesta', models.TextField()),
                ('orden', models.PositiveIntegerField(default=0)),
                ('activa', models.BooleanField(default=True)),
            ],
            options={'verbose_name': 'pregunta frecuente', 'verbose_name_plural': 'preguntas frecuentes', 'ordering': ('orden', 'id')},
        ),
        migrations.CreateModel(
            name='MensajeContacto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=120)),
                ('email', models.EmailField(max_length=254)),
                ('telefono', models.CharField(blank=True, max_length=40)),
                ('asunto', models.CharField(max_length=100)),
                ('mensaje', models.TextField()),
                ('urgente', models.BooleanField(default=False)),
                ('estado', models.CharField(choices=[('nuevo', 'Nuevo'), ('en_proceso', 'En proceso'), ('respondido', 'Respondido'), ('archivado', 'Archivado')], default='nuevo', max_length=20)),
                ('notas_internas', models.TextField(blank=True)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('actualizado', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'mensaje de contacto', 'verbose_name_plural': 'mensajes de contacto', 'ordering': ('-urgente', '-creado')},
        ),
    ]
