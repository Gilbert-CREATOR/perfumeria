from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.text import slugify


class ConfiguracionSitio(models.Model):
    marca = models.CharField(max_length=80, default='D.A.R.C.Y.')
    titulo_home = models.CharField(max_length=120, default='D.A.R.C.Y.')
    texto_nosotros = models.TextField(
        blank=True,
        default='Minimalist design meets exceptional fragrance. We believe in the power of simplicity and the art of perfumery.',
    )
    texto_filosofia = models.TextField(
        blank=True,
        default='At D.A.R.C.Y., we believe that less is more. We remove the unnecessary to reveal the true essence of each scent.',
    )
    texto_artesania = models.TextField(
        blank=True,
        default='We work with carefully selected ingredients, combining traditional perfumery with modern minimalist design.',
    )
    valor_1_titulo = models.CharField(max_length=80, default='Simplicity')
    valor_1_texto = models.CharField(max_length=240, default='Stripping away the unnecessary to reveal true beauty')
    valor_2_titulo = models.CharField(max_length=80, default='Quality')
    valor_2_texto = models.CharField(max_length=240, default='Only the finest ingredients and craftsmanship')
    valor_3_titulo = models.CharField(max_length=80, default='Innovation')
    valor_3_texto = models.CharField(max_length=240, default='Pushing boundaries while respecting tradition')
    texto_estudio = models.TextField(
        blank=True,
        default='Visit our studio to explore the collection and discover your signature scent.',
    )
    direccion_linea_1 = models.CharField(max_length=160, default='CLEVENKA 33 DK')
    direccion_linea_2 = models.CharField(max_length=160, default='Santiago, RD', blank=True)
    email_contacto = models.EmailField(default='info@darcy.com')
    telefono_contacto = models.CharField(max_length=40, default='+11233455678')
    whatsapp = models.CharField(max_length=40, blank=True)
    horario_semana = models.CharField(max_length=100, default='9:00 AM - 7:00 PM')
    horario_sabado = models.CharField(max_length=100, default='9:00 AM - 5:00 PM')
    horario_domingo = models.CharField(max_length=100, default='Cerrado')
    instagram_url = models.URLField(blank=True, default='https://www.instagram.com/')
    facebook_url = models.URLField(blank=True, default='https://www.facebook.com/')
    twitter_url = models.URLField(blank=True, default='https://x.com/')
    mapa_embed_url = models.URLField(blank=True, max_length=1000)
    texto_politica_envios = models.TextField(blank=True)
    texto_terminos = models.TextField(blank=True)
    mostrar_newsletter = models.BooleanField(default=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'configuración del sitio'
        verbose_name_plural = 'configuración del sitio'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def cargar(cls):
        objeto, _ = cls.objects.get_or_create(pk=1)
        return objeto

    def __str__(self):
        return self.marca


class DisenoCorreo(models.Model):
    validar_color = RegexValidator(
        regex=r'^#[0-9A-Fa-f]{6}$',
        message='Usa un color hexadecimal de 6 dígitos, por ejemplo #A31523.',
    )

    marca = models.CharField(max_length=80, default='D.A.R.C.Y.', verbose_name='Marca del encabezado')
    descriptor = models.CharField(
        max_length=80,
        default='PERFUMERÍA\nCURADA · RD',
        verbose_name='Descriptor del encabezado',
        help_text='Usa un salto de línea para dividirlo en dos renglones.',
    )
    logo_url = models.URLField(
        max_length=1000,
        blank=True,
        verbose_name='URL del logo (opcional)',
        help_text='Debe ser una URL pública HTTPS. Si se deja vacío se muestra el nombre de la marca.',
    )
    color_acento = models.CharField(max_length=7, default='#A31523', validators=[validar_color], verbose_name='Color de acento')
    color_fondo = models.CharField(max_length=7, default='#DDD8D0', validators=[validar_color], verbose_name='Fondo exterior')
    color_contenido = models.CharField(max_length=7, default='#F3F1ED', validators=[validar_color], verbose_name='Fondo del correo')
    color_superficie = models.CharField(max_length=7, default='#E6E1D9', validators=[validar_color], verbose_name='Tarjetas y bloques')
    color_texto = models.CharField(max_length=7, default='#000000', validators=[validar_color], verbose_name='Texto principal')
    color_texto_secundario = models.CharField(max_length=7, default='#57534D', validators=[validar_color], verbose_name='Texto secundario')
    color_borde = models.CharField(max_length=7, default='#D8D3CB', validators=[validar_color], verbose_name='Bordes')
    color_pie = models.CharField(max_length=7, default='#111111', validators=[validar_color], verbose_name='Fondo del pie')
    color_texto_pie = models.CharField(max_length=7, default='#F3F1ED', validators=[validar_color], verbose_name='Texto del pie')
    etiqueta_pie = models.CharField(max_length=80, default='D.A.R.C.Y. JOURNAL', verbose_name='Etiqueta del pie')
    titulo_pie = models.CharField(max_length=120, default='Tu aroma. Tu momento.', verbose_name='Título del pie')
    texto_pie = models.TextField(
        default='Una selección de fragancias para cada temporada, cada hora y cada historia.',
        verbose_name='Descripción del pie',
    )
    texto_boton = models.CharField(max_length=80, default='EXPLORAR CATÁLOGO', verbose_name='Texto del botón')
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'diseño de correo'
        verbose_name_plural = 'diseño de correos'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def cargar(cls):
        objeto, _ = cls.objects.get_or_create(pk=1)
        return objeto

    def __str__(self):
        return f'Diseño de correos · {self.marca}'


class PreguntaFrecuente(models.Model):
    pregunta = models.CharField(max_length=240)
    respuesta = models.TextField()
    orden = models.PositiveIntegerField(default=0)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ('orden', 'id')
        verbose_name = 'pregunta frecuente'
        verbose_name_plural = 'preguntas frecuentes'

    def __str__(self):
        return self.pregunta


class MensajeContacto(models.Model):
    ESTADOS = (
        ('nuevo', 'Nuevo'),
        ('en_proceso', 'En proceso'),
        ('respondido', 'Respondido'),
        ('archivado', 'Archivado'),
    )
    nombre = models.CharField(max_length=120)
    email = models.EmailField()
    telefono = models.CharField(max_length=40, blank=True)
    asunto = models.CharField(max_length=100)
    mensaje = models.TextField()
    urgente = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='nuevo')
    notas_internas = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-urgente', '-creado')
        verbose_name = 'mensaje de contacto'
        verbose_name_plural = 'mensajes de contacto'

    def __str__(self):
        return f'{self.nombre}: {self.asunto}'


class RegistroAuditoria(models.Model):
    usuario = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='acciones_administrativas',
    )
    metodo = models.CharField(max_length=10)
    ruta = models.CharField(max_length=500)
    vista = models.CharField(max_length=120, blank=True)
    estado_http = models.PositiveSmallIntegerField(default=200)
    ip = models.GenericIPAddressField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-creado',)
        verbose_name = 'registro de auditoría'
        verbose_name_plural = 'registros de auditoría'

    def __str__(self):
        actor = self.usuario.username if self.usuario else 'Usuario eliminado'
        return f'{actor} {self.metodo} {self.ruta}'


class ArticuloBlog(models.Model):
    titulo = models.CharField(max_length=180)
    slug = models.SlugField(max_length=210, unique=True, blank=True)
    resumen = models.CharField(max_length=300, blank=True)
    contenido = models.TextField()
    imagen_url = models.URLField(max_length=1000, blank=True)
    publicado = models.BooleanField(default=False)
    publicado_en = models.DateTimeField(null=True, blank=True)
    autor = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-publicado_en', '-creado')

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo) or 'articulo'
            slug = base
            numero = 2
            while ArticuloBlog.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f'{base}-{numero}'
                numero += 1
            self.slug = slug
        if self.publicado and not self.publicado_en:
            self.publicado_en = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo
