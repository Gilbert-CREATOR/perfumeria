from .models import Favorito


def favoritos_usuario(request):
    if not request.user.is_authenticated:
        return {'favoritos_ids': set(), 'favoritos_count': 0}

    ids = set(
        Favorito.objects.filter(usuario=request.user).values_list('producto_id', flat=True)
    )
    return {'favoritos_ids': ids, 'favoritos_count': len(ids)}
