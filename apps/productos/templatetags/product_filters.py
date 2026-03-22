from django import template

register = template.Library()

@register.filter
def format_price(price):
    """Formatear precio para que sea más legible"""
    if price:
        return f"${price:,.0f}".replace(",", ",")
    return "$0"
