from django import template

register = template.Library()


@register.filter
def estado_color(estado):
    colores = {
        'pendiente': 'secondary',
        'pagado': 'success',
        'enviado': 'warning',
        'entregado': 'primary',
        'cancelado': 'danger',
    }
    return colores.get(estado, 'secondary')


@register.filter
def mul(value, arg):
    return value * arg


@register.filter
def estrellas(rating):
    estrellas_html = ""
    for i in range(1, 6):
        if i <= rating:
            estrellas_html += '<i class="fas fa-star text-warning"></i>'
        elif i - 0.5 <= rating:
            estrellas_html += '<i class="fas fa-star-half-alt text-warning"></i>'
        else:
            estrellas_html += '<i class="far fa-star text-warning"></i>'
    return estrellas_html
