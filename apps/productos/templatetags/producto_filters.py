from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def formato_precio(valor):
    """
    Formatea el precio de 3200,00 a 3,200
    """
    if isinstance(valor, (int, float, Decimal)):
        return f"{valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return valor
