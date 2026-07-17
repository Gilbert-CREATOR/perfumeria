from django.db import OperationalError, ProgrammingError

from .models import ConfiguracionSitio


def configuracion_sitio(request):
    try:
        configuracion = ConfiguracionSitio.cargar()
    except (OperationalError, ProgrammingError):
        configuracion = ConfiguracionSitio()
    return {'configuracion_sitio': configuracion}
