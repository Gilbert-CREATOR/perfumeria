import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse

from apps.productos.models import Producto
from .models import Carrito, Envio, ItemCarrito, ItemPedido, MetodoEnvio, Pedido
from .services import PENDING_CART_SESSION_KEY


class PendingCartAuthenticationTests(TestCase):
    def setUp(self):
        self.producto = Producto.objects.create(
            nombre='Serum pendiente',
            marca='Darcy',
            precio='1200.00',
            stock=5,
            disponible=True,
        )

    def request_add(self, quantity=1):
        return self.client.post(
            reverse('agregar_al_carrito', args=[self.producto.id]),
            data=json.dumps({'cantidad': quantity}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

    def test_login_completa_el_producto_pendiente_con_su_cantidad(self):
        user = User.objects.create_user(username='cliente', password='clave-segura-123')

        add_response = self.request_add(quantity=2)
        self.assertEqual(add_response.status_code, 200)
        self.assertFalse(add_response.json()['success'])
        self.assertIn('/usuarios/login/', add_response.json()['redirect'])
        self.assertEqual(self.client.session[PENDING_CART_SESSION_KEY]['quantity'], 2)
        self.assertFalse(Carrito.objects.filter(usuario=user).exists())

        login_response = self.client.post(
            reverse('login'),
            {'username': 'cliente', 'password': 'clave-segura-123'},
        )
        self.assertRedirects(login_response, reverse('ver_carrito'), fetch_redirect_response=False)

        item = ItemCarrito.objects.get(carrito__usuario=user, producto=self.producto)
        self.assertEqual(item.cantidad, 2)
        self.assertNotIn(PENDING_CART_SESSION_KEY, self.client.session)

    def test_registro_completa_el_producto_pendiente(self):
        self.request_add(quantity=1)

        register_response = self.client.post(
            reverse('register'),
            {
                'username': 'cliente_nuevo',
                'email': 'nuevo@example.com',
                'first_name': 'Cliente',
                'last_name': 'Nuevo',
                'password1': 'clave-segura-123',
                'password2': 'clave-segura-123',
                'terms_accepted': 'on',
            },
        )
        self.assertRedirects(register_response, reverse('ver_carrito'), fetch_redirect_response=False)

        item = ItemCarrito.objects.get(
            carrito__usuario__username='cliente_nuevo',
            producto=self.producto,
        )
        self.assertEqual(item.cantidad, 1)

    def test_login_fallido_no_agrega_el_producto(self):
        User.objects.create_user(username='cliente', password='clave-segura-123')
        self.request_add(quantity=1)

        with patch('apps.usuarios.views.render', return_value=HttpResponse(status=200)):
            response = self.client.post(
                reverse('login'),
                {'username': 'cliente', 'password': 'incorrecta'},
            )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ItemCarrito.objects.exists())
        self.assertIn(PENDING_CART_SESSION_KEY, self.client.session)

    def test_usuario_autenticado_agrega_la_cantidad_solicitada(self):
        user = User.objects.create_user(username='cliente', password='clave-segura-123')
        self.client.force_login(user)

        response = self.request_add(quantity=3)

        self.assertTrue(response.json()['success'])
        self.assertEqual(
            ItemCarrito.objects.get(carrito__usuario=user, producto=self.producto).cantidad,
            3,
        )

    def test_detalle_entrega_cookie_csrf_a_visitante_anonimo(self):
        with patch('apps.productos.views.render', return_value=HttpResponse(status=200)):
            response = self.client.get(
                reverse('detalle_producto', args=[self.producto.id])
            )

        self.assertIn('csrftoken', response.cookies)

    def test_flujo_anonimo_funciona_con_proteccion_csrf_real(self):
        secure_client = Client(enforce_csrf_checks=True)
        with patch('apps.productos.views.render', return_value=HttpResponse(status=200)):
            detail_response = secure_client.get(
                reverse('detalle_producto', args=[self.producto.id])
            )
        csrf_token = detail_response.cookies['csrftoken'].value

        response = secure_client.post(
            reverse('agregar_al_carrito', args=[self.producto.id]),
            data=json.dumps({'cantidad': 1}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('/usuarios/login/', response.json()['redirect'])


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
            temporada=['night', 'winter'],
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
