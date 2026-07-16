import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.http import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.productos.models import AlertaStock, Producto, Resena
from .models import Carrito, Envio, ItemCarrito, ItemPedido, MetodoEnvio, Pedido
from .services import PENDING_CART_SESSION_KEY
from .recommendations import productos_recomendados_por_temporada
from .emails import (
    enviar_email_carrito_abandonado,
    enviar_email_confirmacion_pedido,
    enviar_email_envio_despachado,
    enviar_email_pago_confirmado,
    enviar_email_pedido_entregado,
    enviar_email_pago_rechazado,
    enviar_email_pedido_preparacion,
    enviar_email_cancelacion_reembolso,
    enviar_email_recomendaciones,
    enviar_email_solicitud_resena,
)
from .admin_views import notificar_cambio_envio


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    PUBLIC_SITE_URL='https://darcy.example',
    DEFAULT_FROM_EMAIL='D.A.R.C.Y. <noreply@darcy.example>',
)
class DesignedEmailTemplatesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='cliente_email',
            email='cliente@example.com',
            first_name='Ana',
        )
        self.producto = Producto.objects.create(
            nombre='Noir Intense',
            marca='Darcy',
            precio='3200.00',
            stock=5,
            disponible=True,
            temporada=['noche'],
        )
        self.pedido = Pedido.objects.create(
            usuario=self.user,
            subtotal='3200.00',
            costo_envio='150.00',
            total='3350.00',
            estado='pagado',
            metodo_pago='transferencia',
            nombre_completo='Ana Cliente',
            telefono='8095550101',
            direccion='Calle Principal 10',
            ciudad='Santo Domingo',
            provincia='Distrito Nacional',
            codigo_postal='10101',
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            cantidad=1,
            precio='3200.00',
        )
        metodo = MetodoEnvio.objects.create(
            nombre='Entrega express',
            costo='150.00',
            tiempo_entrega='1 día',
            activo=True,
        )
        Envio.objects.create(
            pedido=self.pedido,
            metodo_envio=metodo,
            numero_seguimiento='DARCY-001',
            estado='despachado',
        )

    def test_los_cinco_correos_se_renderizan_con_diseno_y_enlaces_reales(self):
        carrito = Carrito.objects.create(usuario=self.user)
        item_carrito = ItemCarrito.objects.create(
            carrito=carrito,
            producto=self.producto,
            cantidad=1,
        )

        resultados = [
            enviar_email_confirmacion_pedido(self.pedido),
            enviar_email_pago_confirmado(self.pedido),
            enviar_email_envio_despachado(self.pedido),
            enviar_email_pedido_entregado(self.pedido),
            enviar_email_carrito_abandonado(self.user, [item_carrito]),
        ]

        self.assertEqual(resultados, [True, True, True, True, True])
        self.assertEqual(len(mail.outbox), 5)
        for mensaje in mail.outbox:
            self.assertTrue(mensaje.alternatives)
            html = mensaje.alternatives[0][0]
            self.assertIn('D.A.R.C.Y.', html)
            self.assertIn('#A31523', html)
            self.assertIn('https://darcy.example', html)

    def test_los_nuevos_correos_transaccionales_tambien_tienen_diseno(self):
        Producto.objects.create(
            nombre='Noir Companion', marca='Darcy', precio='2800.00', stock=4,
            disponible=True, temporada=['noche'],
        )
        resultados = [
            enviar_email_pago_rechazado(self.pedido),
            enviar_email_pedido_preparacion(self.pedido),
            enviar_email_cancelacion_reembolso(self.pedido),
            enviar_email_cancelacion_reembolso(self.pedido, reembolsado=True),
            enviar_email_recomendaciones(self.pedido),
            enviar_email_solicitud_resena(self.pedido),
        ]
        self.assertEqual(resultados, [True] * 6)
        self.assertEqual(len(mail.outbox), 6)
        for mensaje in mail.outbox:
            html = mensaje.alternatives[0][0]
            self.assertIn('D.A.R.C.Y.', html)
            self.assertIn('#A31523', html)

    def test_reposicion_de_stock_envia_aviso_una_sola_vez(self):
        self.producto.stock = 0
        self.producto.save(update_fields=['stock'])
        alerta = AlertaStock.objects.create(usuario=self.user, producto=self.producto)
        self.producto.stock = 3
        self.producto.save(update_fields=['stock'])
        alerta.refresh_from_db()
        self.assertIsNotNone(alerta.enviada)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('volvió a estar disponible', mail.outbox[0].subject)


class CartSeasonRecommendationsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='cliente_recomendaciones',
            password='clave-segura-123',
        )
        self.carrito = Carrito.objects.create(usuario=self.user)
        self.en_carrito = Producto.objects.create(
            nombre='Perfume del carrito',
            precio='2500.00',
            stock=5,
            disponible=True,
            temporada=['invierno', 'noche'],
        )
        ItemCarrito.objects.create(
            carrito=self.carrito,
            producto=self.en_carrito,
            cantidad=1,
        )

    def recomendaciones(self):
        items = self.carrito.items.select_related('producto').all()
        return productos_recomendados_por_temporada(items)

    def test_recomienda_por_mayor_numero_de_temporadas_coincidentes(self):
        dos_coincidencias = Producto.objects.create(
            nombre='Afinidad completa',
            precio='2300.00',
            stock=4,
            disponible=True,
            temporada=['invierno', 'noche', 'otono'],
        )
        una_coincidencia = Producto.objects.create(
            nombre='Afinidad parcial',
            precio='1800.00',
            stock=3,
            disponible=True,
            temporada=['noche'],
        )
        Producto.objects.create(
            nombre='Sin afinidad',
            precio='1900.00',
            stock=3,
            disponible=True,
            temporada=['verano', 'dia'],
        )

        self.assertEqual(
            [producto.pk for producto in self.recomendaciones()],
            [dos_coincidencias.pk, una_coincidencia.pk],
        )

    def test_excluye_carrito_inactivos_y_productos_sin_stock(self):
        Producto.objects.create(
            nombre='Inactivo',
            precio='2000.00',
            stock=5,
            disponible=False,
            temporada=['invierno'],
        )
        Producto.objects.create(
            nombre='Agotado',
            precio='2000.00',
            stock=0,
            disponible=True,
            temporada=['noche'],
        )

        self.assertEqual(self.recomendaciones(), [])

    def test_sin_temporadas_en_el_carrito_no_inventa_recomendaciones(self):
        self.en_carrito.temporada = []
        self.en_carrito.save(update_fields=['temporada'])
        Producto.objects.create(
            nombre='Otro perfume',
            precio='2000.00',
            stock=5,
            disponible=True,
            temporada=['noche'],
        )

        self.assertEqual(self.recomendaciones(), [])

    def test_vista_del_carrito_entrega_las_recomendaciones_a_la_plantilla(self):
        recomendado = Producto.objects.create(
            nombre='Recomendado visible',
            precio='2100.00',
            stock=5,
            disponible=True,
            temporada=['invierno'],
        )
        self.client.force_login(self.user)

        with patch('apps.carrito.views.render', return_value=HttpResponse(status=200)) as mocked_render:
            response = self.client.get(reverse('ver_carrito'))

        self.assertEqual(response.status_code, 200)
        contexto = mocked_render.call_args.args[2]
        self.assertEqual(contexto['productos_relacionados'], [recomendado])


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
            temporada=['invierno', 'noche'],
            temporada_porcentajes={'invierno': 80, 'noche': 100},
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
        self.resena = Resena.objects.create(
            usuario=self.admin_user,
            producto=self.producto,
            estrellas=4,
            comentario='Reseña administrable.',
        )

    def test_admin_index_pages_render(self):
        urls = [
            reverse('admin_panel'),
            reverse('admin_productos'),
            reverse('admin_producto_crear'),
            reverse('admin_resenas'),
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
            reverse('admin_resena_editar', args=[self.resena.id]),
            reverse('admin_metodo_envio_editar', args=[self.metodo_envio.id]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_admin_puede_editar_y_eliminar_resena(self):
        response = self.client.post(
            reverse('admin_resena_editar', args=[self.resena.id]),
            {'estrellas': 2, 'comentario': 'Contenido corregido por administración.'},
        )
        self.assertEqual(response.status_code, 302)
        self.resena.refresh_from_db()
        self.assertEqual(self.resena.estrellas, 2)
        self.assertEqual(self.resena.comentario, 'Contenido corregido por administración.')

        response = self.client.post(reverse('admin_resena_eliminar', args=[self.resena.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Resena.objects.filter(pk=self.resena.id).exists())

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

    def test_hitos_del_envio_disparan_el_correo_correspondiente_una_sola_vez(self):
        self.admin_user.email = 'cliente-envio@example.com'
        self.admin_user.save(update_fields=['email'])

        with patch('apps.carrito.admin_views.enviar_email_envio_despachado') as despacho, \
             patch('apps.carrito.admin_views.enviar_email_pedido_entregado') as entrega:
            self.envio.estado = 'despachado'
            notificar_cambio_envio(self.envio, 'preparando')
            despacho.assert_called_once_with(self.pedido)
            entrega.assert_not_called()

            notificar_cambio_envio(self.envio, 'despachado')
            self.assertEqual(despacho.call_count, 1)

            self.envio.estado = 'entregado'
            notificar_cambio_envio(self.envio, 'en_transito')
            entrega.assert_called_once_with(self.pedido)

    def test_admin_can_publish_a_product_with_zero_stock(self):
        producto = Producto.objects.create(
            nombre='Agotado visible',
            stock=0,
            disponible=False,
        )

        response = self.client.post(
            reverse('admin_producto_toggle_disponibilidad', args=[producto.id]),
        )

        self.assertEqual(response.status_code, 302)
        producto.refresh_from_db()
        self.assertTrue(producto.disponible)
