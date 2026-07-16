import uuid

from django.conf import settings
from django.db import models


class SuscriptorNewsletter(models.Model):
    email = models.EmailField(unique=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='suscripciones_newsletter',
    )
    activo = models.BooleanField(default=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    fecha_suscripcion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-fecha_suscripcion',)
        verbose_name = 'suscriptor del newsletter'
        verbose_name_plural = 'suscriptores del newsletter'

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
