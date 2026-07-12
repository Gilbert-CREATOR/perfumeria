from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFilter, ImageOps


MAX_IMAGE_DIMENSION = 1600
BACKGROUND_TOLERANCE = 52
TRANSPARENT_MARKER = (255, 0, 255, 0)


def remove_uniform_background(uploaded_file):
    """Convierte en transparencia el fondo uniforme conectado a los bordes."""
    uploaded_file.seek(0)
    with Image.open(uploaded_file) as source:
        image = ImageOps.exif_transpose(source).convert('RGBA')
        image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)

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

    pixels = working.load()
    alpha = Image.new('L', working.size, 255)
    alpha_pixels = alpha.load()
    for y in range(height):
        for x in range(width):
            if pixels[x, y] == TRANSPARENT_MARKER:
                alpha_pixels[x, y] = 0

    # Suaviza levemente el borde para evitar un recorte dentado.
    alpha = alpha.filter(ImageFilter.GaussianBlur(radius=0.55))
    image.putalpha(alpha)

    output = BytesIO()
    image.save(output, format='PNG', optimize=True)
    output.seek(0)
    original_stem = Path(getattr(uploaded_file, 'name', 'producto')).stem
    return ContentFile(output.read(), name=f'{original_stem}_sin_fondo.png')
