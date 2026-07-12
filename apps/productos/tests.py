import base64
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
                'temporada': 'special',
            },
            files={'imagen': imagen},
        )
        self.assertTrue(form.is_valid(), form.errors)
        producto = form.save()
        producto.refresh_from_db()

        self.assertTrue(producto.imagen_base64)
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
            temporada='special',
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
