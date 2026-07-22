from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def formato_precio(valor):
    """
    Formatea el precio de 13000.00 a 13,000.0.
    """
    if isinstance(valor, (int, float, Decimal)):
        return f"{valor:,.1f}"
    return valor
