from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=20, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"

class Direccion(models.Model):
    TIPO_DIRECCION = [
        ('envio', 'Envío'),
        ('facturacion', 'Facturación'),
        ('ambas', 'Ambas'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='direcciones')
    tipo = models.CharField(max_length=20, choices=TIPO_DIRECCION, default='envio')
    nombre_completo = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=10)
    pais = models.CharField(max_length=50, default='República Dominicana')
    es_predeterminada = models.BooleanField(default=False)
    
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-es_predeterminada', '-creado']
    
    def __str__(self):
        return f"{self.nombre_completo} - {self.direccion}"
    
    def save(self, *args, **kwargs):
        # Si esta dirección es predeterminada, desmarcar las otras
        if self.es_predeterminada:
            Direccion.objects.filter(
                usuario=self.usuario, 
                es_predeterminada=True
            ).exclude(pk=self.pk).update(es_predeterminada=False)
        super().save(*args, **kwargs)
    
    def direccion_completa(self):
        return f"{self.direccion}, {self.ciudad}, {self.provincia}, {self.codigo_postal}, {self.pais}"
