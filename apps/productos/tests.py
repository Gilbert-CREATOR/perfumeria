import base64

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.carrito.admin_forms import ProductoAdminForm
from .models import Producto


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
