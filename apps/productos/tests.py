import base64
from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from apps.carrito.admin_forms import ProductoAdminForm
from .models import Producto
from .image_processing import remove_uniform_background


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
                'temporada': ['summer', 'special'],
            },
            files={'imagen': imagen},
        )
        self.assertTrue(form.is_valid(), form.errors)
        producto = form.save()
        producto.refresh_from_db()

        self.assertTrue(producto.imagen_base64)
        self.assertEqual(producto.temporada, ['summer', 'special'])
        self.assertEqual(producto.get_temporada_display(), 'Summer, Special')
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
            temporada=['special'],
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
                'temporada': producto.temporada,
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
            temporada=['summer', 'day'],
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
                'temporada': producto.temporada,
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
        self.assertFalse(producto.disponible)

    def test_formulario_crea_y_reutiliza_tipo_y_temporadas_personalizadas(self):
        form = ProductoAdminForm(
            data={
                'nombre': 'Serum facial',
                'nuevo_tipo': 'Serum',
                'nueva_temporada': 'Primavera, Todo el año',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        producto = form.save()
        self.assertEqual(producto.tipo, 'Serum')
        self.assertEqual(producto.temporada, ['Primavera', 'Todo el año'])

        siguiente_formulario = ProductoAdminForm()
        self.assertIn(('Serum', 'Serum'), siguiente_formulario.fields['tipo'].choices)
        self.assertIn(
            ('Primavera', 'Primavera'),
            siguiente_formulario.fields['temporada'].choices,
        )
