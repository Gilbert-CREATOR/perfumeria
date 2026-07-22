from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.carrito.models import Pedido

class Command(BaseCommand):
    help = 'Verificar todos los pedidos en la base de datos'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("VERIFICACIÓN DE PEDIDOS EN BASE DE DATOS")
        self.stdout.write("=" * 60)
        
        # Mostrar todos los usuarios
        usuarios = User.objects.all()
        self.stdout.write(f"\nTotal de usuarios: {usuarios.count()}")
        
        for usuario in usuarios:
            self.stdout.write(f"  - {usuario.username} (ID: {usuario.id}) - Staff: {usuario.is_staff}")
        
        # Mostrar todos los pedidos
        pedidos = Pedido.objects.all().order_by('-creado')
        self.stdout.write(f"\nTotal de pedidos en DB: {pedidos.count()}")
        
        if pedidos.exists():
            for pedido in pedidos:
                self.stdout.write(
                    f"\nPedido #{pedido.id}:"
                    f"\n  Usuario: {pedido.usuario.username} (ID: {pedido.usuario.id})"
                    f"\n  Estado: {pedido.estado}"
                    f"\n  Total: ${pedido.total:,.1f}"
                    f"\n  Fecha: {pedido.creado}"
                    f"\n  Items: {pedido.items.count()}"
                    f"\n  Método pago: {pedido.metodo_pago or 'No especificado'}"
                )
                
                # Mostrar items del pedido
                for item in pedido.items.all():
                    self.stdout.write(f"    - {item.producto.nombre} x{item.cantidad} = ${item.subtotal():,.1f}")
        else:
            self.stdout.write("  No hay pedidos en la base de datos")
        
        # Resumen por usuario
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("RESUMEN POR USUARIO:")
        self.stdout.write("=" * 60)
        
        for usuario in usuarios:
            pedidos_usuario = Pedido.objects.filter(usuario=usuario)
            if pedidos_usuario.exists():
                total = sum(p.total for p in pedidos_usuario)
                self.stdout.write(
                    f"\n{usuario.username}:"
                    f"\n  Pedidos: {pedidos_usuario.count()}"
                    f"\n  Total gastado: ${total:,.1f}"
                )
                for pedido in pedidos_usuario:
                    self.stdout.write(f"    - Pedido #{pedido.id}: ${pedido.total:,.1f} ({pedido.get_estado_display()})")
            else:
                self.stdout.write(f"\n{usuario.username}: 0 pedidos")
        
        self.stdout.write("\n" + "=" * 60)
