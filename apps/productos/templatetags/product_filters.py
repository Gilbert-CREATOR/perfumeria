from django import template

register = template.Library()

@register.filter
def format_price(price):
    """Formatear precio para que sea más legible"""
    if price is not None:
        return f"${price:,.1f}"
    return "$0.0"
