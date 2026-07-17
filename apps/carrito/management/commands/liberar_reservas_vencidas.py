from django.core.management.base import BaseCommand
from apps.carrito.services import liberar_reservas_vencidas


class Command(BaseCommand):
    help = 'Cancela pedidos pendientes vencidos y reintegra su inventario una sola vez.'

    def handle(self, *args, **options):
        liberados = liberar_reservas_vencidas(limite=1000)

        self.stdout.write(self.style.SUCCESS(
            f'{liberados} reserva(s) vencida(s) liberada(s).'
        ))
