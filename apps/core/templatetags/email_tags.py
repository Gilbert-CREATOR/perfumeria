from django import template
from django.db.utils import OperationalError, ProgrammingError

from apps.core.models import DisenoCorreo

register = template.Library()


@register.simple_tag
def diseno_correo():
    try:
        return DisenoCorreo.cargar()
    except (OperationalError, ProgrammingError):
        return DisenoCorreo()
