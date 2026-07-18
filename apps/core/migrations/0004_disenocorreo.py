from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_articuloblog'),
    ]

    operations = [
        migrations.CreateModel(
            name='DisenoCorreo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('marca', models.CharField(default='D.A.R.C.Y.', max_length=80, verbose_name='Marca del encabezado')),
                ('descriptor', models.CharField(default='PERFUMERÍA\nCURADA · RD', help_text='Usa un salto de línea para dividirlo en dos renglones.', max_length=80, verbose_name='Descriptor del encabezado')),
                ('logo_url', models.URLField(blank=True, help_text='Debe ser una URL pública HTTPS. Si se deja vacío se muestra el nombre de la marca.', max_length=1000, verbose_name='URL del logo (opcional)')),
                ('color_acento', models.CharField(default='#A31523', max_length=7, validators=[django.core.validators.RegexValidator(message='Usa un color hexadecimal de 6 dígitos, por ejemplo #A31523.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Color de acento')),
                ('color_fondo', models.CharField(default='#DDD8D0', max_length=7, validators=[django.core.validators.RegexValidator(message='Usa un color hexadecimal de 6 dígitos, por ejemplo #A31523.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Fondo exterior')),
                ('color_contenido', models.CharField(default='#F3F1ED', max_length=7, validators=[django.core.validators.RegexValidator(message='Usa un color hexadecimal de 6 dígitos, por ejemplo #A31523.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Fondo del correo')),
                ('color_superficie', models.CharField(default='#E6E1D9', max_length=7, validators=[django.core.validators.RegexValidator(message='Usa un color hexadecimal de 6 dígitos, por ejemplo #A31523.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Tarjetas y bloques')),
                ('color_texto', models.CharField(default='#000000', max_length=7, validators=[django.core.validators.RegexValidator(message='Usa un color hexadecimal de 6 dígitos, por ejemplo #A31523.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Texto principal')),
                ('color_texto_secundario', models.CharField(default='#57534D', max_length=7, validators=[django.core.validators.RegexValidator(message='Usa un color hexadecimal de 6 dígitos, por ejemplo #A31523.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Texto secundario')),
                ('color_borde', models.CharField(default='#D8D3CB', max_length=7, validators=[django.core.validators.RegexValidator(message='Usa un color hexadecimal de 6 dígitos, por ejemplo #A31523.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Bordes')),
                ('color_pie', models.CharField(default='#111111', max_length=7, validators=[django.core.validators.RegexValidator(message='Usa un color hexadecimal de 6 dígitos, por ejemplo #A31523.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Fondo del pie')),
                ('color_texto_pie', models.CharField(default='#F3F1ED', max_length=7, validators=[django.core.validators.RegexValidator(message='Usa un color hexadecimal de 6 dígitos, por ejemplo #A31523.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Texto del pie')),
                ('etiqueta_pie', models.CharField(default='D.A.R.C.Y. JOURNAL', max_length=80, verbose_name='Etiqueta del pie')),
                ('titulo_pie', models.CharField(default='Tu aroma. Tu momento.', max_length=120, verbose_name='Título del pie')),
                ('texto_pie', models.TextField(default='Una selección de fragancias para cada temporada, cada hora y cada historia.', verbose_name='Descripción del pie')),
                ('texto_boton', models.CharField(default='EXPLORAR CATÁLOGO', max_length=80, verbose_name='Texto del botón')),
                ('actualizado', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'diseño de correo', 'verbose_name_plural': 'diseño de correos'},
        ),
    ]
