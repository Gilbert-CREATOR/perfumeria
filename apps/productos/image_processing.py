from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFilter, ImageOps


MAX_IMAGE_DIMENSION = 1200
MAX_SOURCE_PIXELS = 20_000_000
BACKGROUND_TOLERANCE = 52
TRANSPARENT_MARKER = (255, 0, 255, 0)


def validate_product_image(uploaded_file):
    """Valida el archivo sin conservar la imagen completa en memoria."""
    uploaded_file.seek(0)
    try:
        try:
            with Image.open(uploaded_file) as source:
                width, height = source.size
                if width <= 0 or height <= 0 or width * height > MAX_SOURCE_PIXELS:
                    raise ValueError('La imagen tiene dimensiones demasiado grandes.')
                source.verify()
        except Image.DecompressionBombError as exc:
            raise ValueError('La imagen tiene dimensiones demasiado grandes.') from exc
    finally:
        uploaded_file.seek(0)


def remove_uniform_background(uploaded_file):
    """Convierte en transparencia el fondo uniforme conectado a los bordes."""
    validate_product_image(uploaded_file)
    with Image.open(uploaded_file) as source:
        source = ImageOps.exif_transpose(source)
        source.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
        image = source.convert('RGBA')

    # Flood fill desde cada esquina: solo elimina colores similares que estén
    # conectados al borde, evitando borrar zonas internas del producto.
    working = image.copy()
    width, height = working.size
    for corner in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
        ImageDraw.floodfill(
            working,
            corner,
            TRANSPARENT_MARKER,
            thresh=BACKGROUND_TOLERANCE,
        )

    # El marcador usa alfa 0. Extraer ese canal con Pillow evita recorrer
    # millones de píxeles desde Python y mantiene rápido el worker de Render.
    alpha = working.getchannel('A').filter(ImageFilter.GaussianBlur(radius=0.55))
    image.putalpha(alpha)

    output = BytesIO()
    image.save(output, format='PNG', compress_level=6)
    output.seek(0)
    original_stem = Path(getattr(uploaded_file, 'name', 'producto')).stem
    return ContentFile(output.read(), name=f'{original_stem}_sin_fondo.png')
