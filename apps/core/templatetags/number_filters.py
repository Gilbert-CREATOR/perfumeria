from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def formato_numero(valor):
    """Muestra importes con miles separados por coma y un decimal."""
    if valor in (None, ""):
        return "0.0"

    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        return valor

    return f"{numero:,.1f}"
