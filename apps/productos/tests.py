import base64
from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from PIL import Image

from apps.carrito.admin_forms import ProductoAdminForm
from apps.carrito.models import ItemPedido, Pedido
from .models import AlertaStock, Producto, Resena
from .image_processing import MAX_IMAGE_DIMENSION, remove_uniform_background
from .views import catalog_season_options, sort_catalog_products


class AlertasYResenasTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='comprador', email='comprador@example.com', password='clave-segura-123'
        )
        self.producto = Producto.objects.create(
            nombre='Fragancia agotada', precio='1900.00', stock=0, disponible=True,
        )
        self.client.force_login(self.user)

    def test_cliente_puede_activar_alerta_de_stock(self):
        response = self.client.post(reverse('crear_alerta_stock', args=[self.producto.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AlertaStock.objects.filter(usuario=self.user, producto=self.producto).exists())

    def test_solo_comprador_con_pedido_entregado_puede_resenar(self):
        pedido = Pedido.objects.create(usuario=self.user, total='1900.00', estado='entregado')
        ItemPedido.objects.create(
            pedido=pedido, producto=self.producto, cantidad=1, precio='1900.00'
        )
        response = self.client.post(reverse('crear_resena', args=[self.producto.id]), {
            'estrellas': 5, 'comentario': 'Excelente fragancia.',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Resena.objects.filter(
            usuario=self.user, producto=self.producto, estrellas=5
        ).exists())


class ProductoImagenPersistenteTests(TestCase):
    PNG_1X1 = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC'
        'AAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
    )

    def test_formulario_guarda_imagen_en_base_de_datos_y_la_sirve(self):
        imagen = SimpleUploadedFile('perfume.png', self.PNG_1X1, content_type='image/png')
        form = ProductoAdminForm(
            data={
                'nombre': 'Persistente',
                'marca': 'Darcy',
                'descripcion': 'Imagen persistente',
                'precio': '1000.00',
                'tipo': 'eau_de_parfum',
                'tamano_ml': 100,
                'stock': 2,
                'disponible': True,
                'porcentaje_verano': 80,
                'porcentaje_otono': 45,
            },
            files={'imagen': imagen},
        )
        self.assertTrue(form.is_valid(), form.errors)
        producto = form.save()
        producto.refresh_from_db()

        self.assertTrue(producto.imagen_base64)
        self.assertEqual(producto.temporada, ['verano', 'otono'])
        self.assertEqual(producto.temporada_porcentajes['verano'], 80)
        self.assertEqual(producto.get_temporada_display(), 'Verano, Otoño')
        self.assertIn('?v=', producto.imagen_url_property)
        response = self.client.get(reverse('producto_imagen', args=[producto.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertEqual(response.content, self.PNG_1X1)

    def test_formulario_permite_eliminar_la_imagen_actual(self):
        producto = Producto.objects.create(
            nombre='Con imagen',
            marca='Darcy',
            descripcion='Producto para eliminar imagen',
            precio='1000.00',
            imagen='productos/archivo_eliminado_por_render.png',
            imagen_base64=base64.b64encode(self.PNG_1X1).decode('ascii'),
            imagen_nombre='perfume.png',
            tipo='eau_de_parfum',
            tamano_ml=100,
            stock=2,
            disponible=True,
            temporada=['otono'],
            temporada_porcentajes={'otono': 70},
        )
        form = ProductoAdminForm(
            data={
                'nombre': producto.nombre,
                'marca': producto.marca,
                'descripcion': producto.descripcion,
                'precio': producto.precio,
                'tipo': producto.tipo,
                'tamano_ml': producto.tamano_ml,
                'stock': producto.stock,
                'disponible': True,
                'porcentaje_otono': 70,
                'eliminar_imagen': True,
            },
            instance=producto,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        producto.refresh_from_db()

        self.assertFalse(producto.imagen)
        self.assertIsNone(producto.imagen_base64)
        self.assertIsNone(producto.imagen_nombre)

    def test_formulario_reprocesa_el_fondo_de_la_imagen_actual(self):
        source = Image.new('RGB', (40, 40), 'white')
        for x in range(12, 28):
            for y in range(8, 34):
                source.putpixel((x, y), (10, 80, 130))
        buffer = BytesIO()
        source.save(buffer, format='PNG')
        producto = Producto.objects.create(
            nombre='Fondo anterior',
            marca='Darcy',
            descripcion='Imagen para reprocesar',
            precio='1000.00',
            imagen_base64=base64.b64encode(buffer.getvalue()).decode('ascii'),
            imagen_nombre='fondo.png',
            tipo='eau_de_parfum',
            tamano_ml=100,
            stock=2,
            disponible=True,
            temporada=['verano', 'dia'],
            temporada_porcentajes={'verano': 65, 'dia': 90},
        )
        form = ProductoAdminForm(
            data={
                'nombre': producto.nombre,
                'marca': producto.marca,
                'descripcion': producto.descripcion,
                'precio': producto.precio,
                'tipo': producto.tipo,
                'tamano_ml': producto.tamano_ml,
                'stock': producto.stock,
                'disponible': True,
                'porcentaje_verano': 65,
                'porcentaje_dia': 90,
                'quitar_fondo': True,
            },
            instance=producto,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        producto.refresh_from_db()

        result = Image.open(BytesIO(base64.b64decode(producto.imagen_base64))).convert('RGBA')
        self.assertEqual(result.getpixel((0, 0))[3], 0)
        self.assertTrue(producto.imagen_nombre.endswith('_sin_fondo.png'))

    def test_eliminador_convierte_fondo_blanco_en_transparente(self):
        source = Image.new('RGB', (40, 40), 'white')
        for x in range(12, 28):
            for y in range(8, 34):
                source.putpixel((x, y), (10, 80, 130))
        buffer = BytesIO()
        source.save(buffer, format='JPEG', quality=95)
        upload = SimpleUploadedFile('perfume.jpg', buffer.getvalue(), content_type='image/jpeg')

        processed = remove_uniform_background(upload)
        result = Image.open(processed).convert('RGBA')

        self.assertEqual(result.getpixel((0, 0))[3], 0)
        self.assertGreater(result.getpixel((20, 20))[3], 200)
        self.assertTrue(processed.name.endswith('_sin_fondo.png'))

    def test_eliminador_redimensiona_imagen_grande_antes_de_guardarla(self):
        source = Image.new('RGB', (1800, 1400), 'white')
        source.paste((20, 90, 150), (650, 300, 1150, 1200))
        buffer = BytesIO()
        source.save(buffer, format='JPEG', quality=88)
        upload = SimpleUploadedFile('grande.jpg', buffer.getvalue(), content_type='image/jpeg')

        processed = remove_uniform_background(upload)
        result = Image.open(processed).convert('RGBA')

        self.assertLessEqual(max(result.size), MAX_IMAGE_DIMENSION)
        self.assertEqual(result.getpixel((0, 0))[3], 0)
        self.assertGreater(result.getpixel((result.width // 2, result.height // 2))[3], 200)

    def test_producto_puede_crearse_con_todos_los_campos_vacios(self):
        form = ProductoAdminForm(data={})

        self.assertTrue(form.is_valid(), form.errors)
        producto = form.save()

        self.assertEqual(producto.nombre, '')
        self.assertEqual(producto.marca, '')
        self.assertEqual(producto.precio, Decimal('0'))
        self.assertEqual(producto.tipo, '')
        self.assertEqual(producto.tamano_ml, 0)
        self.assertEqual(producto.stock, 0)
        self.assertEqual(producto.temporada, [])
        self.assertEqual(producto.temporada_porcentajes, {
            'invierno': 0,
            'primavera': 0,
            'verano': 0,
            'otono': 0,
            'dia': 0,
            'noche': 0,
        })
        self.assertFalse(producto.disponible)

    def test_producto_agotado_puede_seguir_publicado_en_catalogo(self):
        form = ProductoAdminForm(
            data={
                'nombre': 'One Million Elixir',
                'stock': 0,
                'disponible': True,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        producto = form.save()

        self.assertEqual(producto.stock, 0)
        self.assertTrue(producto.disponible)
        self.assertTrue(Producto.objects.filter(disponible=True, pk=producto.pk).exists())

    def test_ultima_unidad_agota_pero_no_oculta_el_producto(self):
        producto = Producto.objects.create(
            nombre='Última unidad',
            stock=1,
            disponible=True,
        )

        self.assertTrue(producto.descontar_stock(1))
        producto.refresh_from_db()

        self.assertEqual(producto.stock, 0)
        self.assertTrue(producto.disponible)
        self.assertFalse(producto.validar_stock(1))

    def test_formulario_guarda_tipo_nuevo_y_porcentajes_de_temporada(self):
        form = ProductoAdminForm(
            data={
                'nombre': 'Serum facial',
                'nuevo_tipo': 'Serum',
                'porcentaje_primavera': 75,
                'porcentaje_dia': 30,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        producto = form.save()
        self.assertEqual(producto.tipo, 'Serum')
        self.assertEqual(producto.temporada, ['primavera', 'dia'])
        self.assertEqual(producto.temporada_porcentajes['primavera'], 75)
        self.assertEqual(producto.temporada_porcentajes['dia'], 30)

        siguiente_formulario = ProductoAdminForm()
        self.assertIn(('Serum', 'Serum'), siguiente_formulario.fields['tipo'].choices)
        opciones_catalogo = catalog_season_options()
        self.assertEqual(opciones_catalogo, [
            ('invierno', 'INVIERNO'),
            ('primavera', 'PRIMAVERA'),
            ('verano', 'VERANO'),
            ('otono', 'OTOÑO'),
            ('dia', 'DÍA'),
            ('noche', 'NOCHE'),
        ])

    def test_metricas_visuales_mantienen_orden_y_porcentajes_seguros(self):
        producto = Producto(
            temporada=['invierno', 'noche'],
            temporada_porcentajes={'invierno': 50, 'noche': 150},
        )

        metricas = producto.temporadas_visual

        self.assertEqual([item['etiqueta'] for item in metricas], [
            'Invierno', 'Primavera', 'Verano', 'Otoño', 'Día', 'Noche',
        ])
        self.assertEqual(metricas[0]['porcentaje'], 50)
        self.assertEqual(metricas[-1]['porcentaje'], 100)

    def test_catalogo_ordena_por_nombre_y_precio(self):
        Producto.objects.create(nombre='Zulu', precio='500.00', disponible=True)
        Producto.objects.create(nombre='alfa', precio='900.00', disponible=True)
        Producto.objects.create(nombre='Beta', precio='100.00', disponible=True)
        productos = Producto.objects.filter(disponible=True)

        por_nombre = sort_catalog_products(productos, 'nombre')
        self.assertEqual(list(por_nombre.values_list('nombre', flat=True)), ['alfa', 'Beta', 'Zulu'])

        por_precio = sort_catalog_products(productos, 'precio_desc')
        self.assertEqual(list(por_precio.values_list('precio', flat=True)), [
            Decimal('900.00'), Decimal('500.00'), Decimal('100.00'),
        ])
