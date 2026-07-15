from apps.productos.models import Producto


def productos_recomendados_por_temporada(items, limite=4):
    """Recomienda productos disponibles que compartan temporadas con los artículos."""
    items = list(items)
    productos_excluidos = {item.producto_id for item in items}
    temporadas_origen = set()

    for item in items:
        temporadas = item.producto.temporada or []
        if isinstance(temporadas, str):
            temporadas = [temporadas]
        temporadas_origen.update(temporada for temporada in temporadas if temporada)

    if not temporadas_origen:
        return []

    candidatos = Producto.objects.filter(
        disponible=True,
        stock__gt=0,
    ).exclude(pk__in=productos_excluidos)

    puntuados = []
    for producto in candidatos:
        temporadas = producto.temporada or []
        if isinstance(temporadas, str):
            temporadas = [temporadas]
        coincidencias = temporadas_origen.intersection(temporadas)
        if coincidencias:
            puntuados.append((len(coincidencias), producto.pk, producto))

    puntuados.sort(key=lambda resultado: (-resultado[0], resultado[1]))
    return [producto for _, _, producto in puntuados[:limite]]
