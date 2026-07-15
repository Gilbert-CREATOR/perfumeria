from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import AlertaStock, Producto


@receiver(pre_save, sender=Producto)
def recordar_stock_anterior(sender, instance, **kwargs):
    if not instance.pk:
        instance._stock_anterior = None
        return
    instance._stock_anterior = sender.objects.filter(pk=instance.pk).values_list('stock', flat=True).first()


@receiver(post_save, sender=Producto)
def avisar_reposicion_stock(sender, instance, created, **kwargs):
    anterior = getattr(instance, '_stock_anterior', None)
    if anterior != 0 or instance.stock <= 0 or not instance.disponible:
        return

    from apps.carrito.emails import enviar_email_producto_disponible

    alertas = AlertaStock.objects.filter(producto=instance, enviada__isnull=True).select_related('usuario')
    for alerta in alertas:
        if enviar_email_producto_disponible(alerta.usuario, instance):
            alerta.enviada = timezone.now()
            alerta.save(update_fields=['enviada'])
