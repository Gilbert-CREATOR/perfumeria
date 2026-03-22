from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.productos.models import Producto
from .models import Envio, ItemPedido, MetodoEnvio, Pedido


class AdminPanelViewsTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin_html',
            password='segura123',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.admin_user)

        self.producto = Producto.objects.create(
            nombre='Noir Absolu',
            marca='Maison Darcy',
            descripcion='Fragancia intensa para pruebas de panel.',
            precio='2500.00',
            tipo='eau_de_parfum',
            tamano_ml=100,
            stock=8,
            disponible=True,
            temporada='night',
        )
        self.pedido = Pedido.objects.create(
            usuario=self.admin_user,
            total='2650.00',
            subtotal='2500.00',
            costo_envio='150.00',
            estado='pagado',
            metodo_pago='stripe',
            nombre_completo='Cliente Demo',
            telefono='8091234567',
            direccion='Av. Principal 123',
            ciudad='Santo Domingo',
            provincia='Distrito Nacional',
            codigo_postal='10101',
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            cantidad=1,
            precio='2500.00',
        )
        self.metodo_envio = MetodoEnvio.objects.create(
            nombre='Entrega express',
            descripcion='Entrega en 24 horas',
            costo='150.00',
            tiempo_entrega='1 día',
            activo=True,
        )
        self.envio = Envio.objects.create(
            pedido=self.pedido,
            metodo_envio=self.metodo_envio,
            numero_seguimiento='EXP-001',
            estado='preparando',
        )

    def test_admin_index_pages_render(self):
        urls = [
            reverse('admin_panel'),
            reverse('admin_productos'),
            reverse('admin_producto_crear'),
            reverse('admin_pedidos'),
            reverse('admin_stock'),
            reverse('admin_envios'),
            reverse('admin_metodos_envio'),
            reverse('admin_analytics'),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_admin_detail_pages_render(self):
        urls = [
            reverse('admin_detalle_pedido', args=[self.pedido.id]),
            reverse('admin_detalle_envio', args=[self.envio.id]),
            reverse('admin_producto_editar', args=[self.producto.id]),
            reverse('admin_metodo_envio_editar', args=[self.metodo_envio.id]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_admin_stock_update_works_without_django_admin(self):
        response = self.client.post(
            reverse('admin_stock'),
            {
                'accion': 'actualizar_stock',
                'producto_id': self.producto.id,
                'stock': 4,
                'disponible': 'true',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 4)
        self.assertTrue(self.producto.disponible)
