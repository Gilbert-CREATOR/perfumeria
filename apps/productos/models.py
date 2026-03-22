from django.db import models
from django.contrib.auth.models import User

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
    
    nombre = models.CharField(max_length=200)
    marca = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    tamano_ml = models.IntegerField()
    stock = models.IntegerField()
    disponible = models.BooleanField(default=True)
    temporada = models.CharField(max_length=20, choices=TEMPORADA_CHOICES, blank=True)

    def __str__(self):
        return self.nombre
    
    def validar_stock(self, cantidad_solicitada=1):
        """Valida si hay stock suficiente"""
        return self.stock >= cantidad_solicitada and self.disponible
    
    def descontar_stock(self, cantidad):
        """Descuenta stock si hay suficiente"""
        if self.validar_stock(cantidad):
            self.stock -= cantidad
            if self.stock == 0:
                self.disponible = False
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