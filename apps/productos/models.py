from django.db import models
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import base64
import hashlib
import mimetypes
import os
from django.urls import reverse

class Producto(models.Model):

    TIPO_CHOICES = [
        ('eau_de_parfum', 'Eau de Parfum'),
        ('eau_de_toilette', 'Eau de Toilette'),
        ('eau_de_cologne', 'Eau de Cologne'),
        ('body_spray', 'Body Spray'),
    ]
    
    TEMPORADA_CHOICES = [
        ('summer', 'Summer'),
        ('winter', 'Winter'),
        ('night', 'Night'),
        ('day', 'Day'),
        ('special', 'Special'),
    ]
    
    nombre = models.CharField(max_length=200, blank=True, default='')
    marca = models.CharField(max_length=100, blank=True, default='')
    descripcion = models.TextField(blank=True, default='')
    precio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    
    # 🖼️ CAMPOS PARA GUARDAR IMAGEN EN BASE DE DATOS
    imagen_base64 = models.TextField(blank=True, null=True, help_text="Imagen guardada en base64 para persistencia")
    imagen_nombre = models.CharField(max_length=255, blank=True, null=True, help_text="Nombre original del archivo de imagen")
    
    tipo = models.CharField(max_length=100, blank=True, default='')
    tamano_ml = models.IntegerField(blank=True, default=0)
    stock = models.IntegerField(blank=True, default=0)
    disponible = models.BooleanField(default=True)
    temporada = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.nombre or f'Producto #{self.pk or "nuevo"}'

    def get_tipo_display(self):
        labels = dict(self.TIPO_CHOICES)
        return labels.get(self.tipo, self.tipo) or 'Sin tipo'

    def get_temporada_display(self):
        values = self.temporada or []
        if isinstance(values, str):
            values = [values]
        labels = dict(self.TEMPORADA_CHOICES)
        return ', '.join(labels.get(value, value) for value in values)

    def save(self, *args, **kwargs):
        # Mantener el formato nuevo incluso si algún comando o integración
        # antigua todavía envía una sola temporada como texto.
        if isinstance(self.temporada, str):
            self.temporada = [self.temporada] if self.temporada else []

        # Render usa un disco efímero. Guardamos una copia de la imagen en la
        # base de datos antes de que el archivo temporal desaparezca.
        if self.imagen and not getattr(self.imagen, '_committed', True):
            self.imagen.seek(0)
            self.imagen_base64 = base64.b64encode(self.imagen.read()).decode('ascii')
            self.imagen_nombre = os.path.basename(self.imagen.name)
            self.imagen.seek(0)
        super().save(*args, **kwargs)
    
    def _restaurar_imagen_desde_base64(self):
        """Restaurar imagen desde base64 al campo imagen"""
        try:
            if self.imagen_base64:
                # Decodificar base64
                image_data = base64.b64decode(self.imagen_base64)
                
                # Crear ContentFile
                content_file = ContentFile(image_data)
                
                # Guardar en el campo imagen
                nombre_archivo = self.imagen_nombre or f"producto_{self.id}.jpg"
                self.imagen.save(nombre_archivo, content_file, save=False)
                
                print(f"✅ Imagen restaurada desde base64: {nombre_archivo}")
        except Exception as e:
            print(f"❌ Error restaurando imagen desde base64: {str(e)}")
    
    def get_imagen_url(self):
        """Obtener URL de la imagen con fallback"""
        if self.imagen_base64:
            version = hashlib.sha256(self.imagen_base64.encode('ascii')).hexdigest()[:12]
            return f"{reverse('producto_imagen', args=[self.pk])}?v={version}"
        elif self.imagen and hasattr(self.imagen, 'url'):
            return self.imagen.url
        else:
            # Placeholder
            return "https://via.placeholder.com/180x180/f3f1ed/000?text=PERFUME"
    
    @property
    def imagen_url_property(self):
        """Propiedad para usar en templates"""
        return self.get_imagen_url()
    
    def tiene_imagen(self):
        """Verificar si tiene imagen (archivo o base64)"""
        return bool(self.imagen or self.imagen_base64)

    def imagen_content_type(self):
        content_type, _ = mimetypes.guess_type(self.imagen_nombre or '')
        return content_type or 'image/jpeg'
    
    def validar_stock(self, cantidad_solicitada=1):
        """Valida si hay stock suficiente"""
        return self.stock >= cantidad_solicitada and self.disponible
    
    def descontar_stock(self, cantidad):
        """Descuenta stock si hay suficiente"""
        if self.validar_stock(cantidad):
            self.stock -= cantidad
            self.save()
            return True
        return False
    
    def rating_promedio(self):
        """Calcula el rating promedio del producto"""
        resenas = self.resenas.all()
        if not resenas:
            return 0
        total = sum(resena.estrellas for resena in resenas)
        return round(total / len(resenas), 1)
    
    def total_resenas(self):
        """Retorna el total de reseñas"""
        return self.resenas.count()
    
class Favorito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('usuario', 'producto')

class Resena(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='resenas')
    comentario = models.TextField()
    estrellas = models.IntegerField()
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario} - {self.producto}"
