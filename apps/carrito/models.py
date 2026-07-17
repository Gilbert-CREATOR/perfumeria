from django.db import models
from django.contrib.auth.models import User
from apps.productos.models import Producto

METODOS_PAGO = [
    ('contra_entrega', 'Contra entrega'),
    ('transferencia', 'Transferencia bancaria'),
    ('paypal', 'PayPal'),
    ('stripe', 'Stripe'),
    ('azul', 'Azul'),
]

ESTADOS_PEDIDO = [
    ('pendiente', 'Pendiente'),
    ('pagado', 'Pagado'),
    ('enviado', 'Enviado'),
    ('entregado', 'Entregado'),
    ('cancelado', 'Cancelado'),
]


class Carrito(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.producto.precio * self.cantidad
    
    
class Pedido(models.Model):
    usuario = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pedidos',
    )
    creado = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS_PEDIDO, default='pendiente')
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, blank=True, null=True)
    referencia_pago = models.CharField(max_length=160, blank=True, db_index=True)
    stock_reservado = models.BooleanField(default=False)
    stock_reintegrado = models.BooleanField(default=False)
    reserva_expira_en = models.DateTimeField(null=True, blank=True)
    pagado_en = models.DateTimeField(null=True, blank=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    # Campos simples para dirección (temporal)
    nombre_completo = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    provincia = models.CharField(max_length=100, blank=True)
    codigo_postal = models.CharField(max_length=10, blank=True)

    def __str__(self):
        cliente = self.usuario.username if self.usuario else self.nombre_completo or 'Cliente eliminado'
        return f"Pedido #{self.id} - {cliente} ({self.get_estado_display()})"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(
        'productos.Producto', on_delete=models.SET_NULL, null=True, blank=True,
    )
    nombre_producto = models.CharField(max_length=200, blank=True)
    marca_producto = models.CharField(max_length=100, blank=True)
    cantidad = models.PositiveIntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.producto:
            self.nombre_producto = self.nombre_producto or self.producto.nombre
            self.marca_producto = self.marca_producto or self.producto.marca
        super().save(*args, **kwargs)

    @property
    def nombre_visible(self):
        return self.nombre_producto or (self.producto.nombre if self.producto else 'Producto eliminado')

    def subtotal(self):
        return self.precio * self.cantidad


class TransaccionPago(models.Model):
    ESTADOS = [
        ('creada', 'Creada'),
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada'),
        ('reembolsada', 'Reembolsada'),
    ]

    pedido = models.ForeignKey(Pedido, on_delete=models.PROTECT, related_name='transacciones')
    proveedor = models.CharField(max_length=30)
    referencia = models.CharField(max_length=160, unique=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='creada')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default='USD')
    respuesta = models.JSONField(default=dict, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.proveedor} {self.referencia} - {self.estado}'


class MovimientoInventario(models.Model):
    TIPOS = [
        ('reserva', 'Reserva por pedido'),
        ('reintegro', 'Reintegro por cancelacion'),
        ('ajuste', 'Ajuste manual'),
        ('entrada', 'Entrada de inventario'),
        ('salida', 'Salida de inventario'),
    ]

    producto = models.ForeignKey(
        'productos.Producto', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movimientos_inventario',
    )
    producto_nombre = models.CharField(max_length=200)
    pedido = models.ForeignKey(
        Pedido, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movimientos_inventario',
    )
    usuario = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movimientos_inventario_realizados',
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    cantidad = models.IntegerField(
        help_text='Valor positivo para entradas y negativo para salidas.',
    )
    stock_anterior = models.PositiveIntegerField()
    stock_resultante = models.PositiveIntegerField()
    motivo = models.CharField(max_length=240, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado', '-id']

    def __str__(self):
        return f'{self.producto_nombre}: {self.cantidad:+d}'

class MetodoEnvio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    tiempo_entrega = models.CharField(max_length=100)  # ej: "2-3 días hábiles"
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nombre} - ${self.costo}"

class Envio(models.Model):
    ESTADO_ENVIO = [
        ('preparando', 'Preparando'),
        ('despachado', 'Despachado'),
        ('en_transito', 'En Tránsito'),
        ('entregado', 'Entregado'),
        ('devuelto', 'Devuelto'),
    ]
    
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='envio')
    metodo_envio = models.ForeignKey(MetodoEnvio, on_delete=models.PROTECT)
    numero_seguimiento = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_ENVIO, default='preparando')
    
    fecha_despacho = models.DateTimeField(null=True, blank=True)
    fecha_entrega_estimada = models.DateField(null=True, blank=True)
    fecha_entrega_real = models.DateTimeField(null=True, blank=True)
    
    notas = models.TextField(blank=True)
    
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Envío del pedido #{self.pedido.id}"
    
    def save(self, *args, **kwargs):
        # Calcular fecha de entrega estimada
        if not self.fecha_entrega_estimada and self.metodo_envio:
            from datetime import datetime, timedelta
            # Basado en tiempo de entrega (ej: "2-3 días")
            try:
                dias = int(self.metodo_envio.tiempo_entrega.split()[0])
                self.fecha_entrega_estimada = datetime.now().date() + timedelta(days=dias)
            except:
                self.fecha_entrega_estimada = datetime.now().date() + timedelta(days=3)
        
        # Actualizar estado del pedido cuando cambia el estado del envío
        if self.pk:
            old_envio = Envio.objects.get(pk=self.pk)
            if old_envio.estado != self.estado:
                if self.estado == 'entregado':
                    self.pedido.estado = 'entregado'
                    self.pedido.save()
                elif self.estado == 'despachado' and self.pedido.estado == 'pagado':
                    self.pedido.estado = 'enviado'
                    self.pedido.save()
        
        super().save(*args, **kwargs)


class PerfilUsuario(models.Model):
    TIPO_USUARIO = [
        ('admin', 'Administrador'),
        ('empleado', 'Empleado'),
        ('cliente', 'Cliente'),
    ]
    
    usuario = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='perfil')
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO, default='cliente')
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_usuario_display()}"
    
    @property
    def es_admin(self):
        return self.tipo_usuario == 'admin'
    
    @property
    def es_empleado(self):
        return self.tipo_usuario == 'empleado'
    
    @property
    def es_cliente(self):
        return self.tipo_usuario == 'cliente'
    
    @property
    def puede_gestionar_usuarios(self):
        """Solo los administradores pueden gestionar usuarios"""
        return self.tipo_usuario == 'admin'
    
    @property
    def puede_ver_todos_los_pedidos(self):
        """Admin y empleados pueden ver todos los pedidos"""
        return self.tipo_usuario in ['admin', 'empleado']
    
    @property
    def puede_ver_estadisticas(self):
        """Admin y empleados pueden ver estadísticas"""
        return self.tipo_usuario in ['admin', 'empleado']
