from .models import RegistroAuditoria


class AuditoriaAdminMiddleware:
    """Registra mutaciones hechas desde el panel sin guardar datos sensibles."""

    MUTATING_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, 'user', None)
        if (
            request.path.startswith('/admin/')
            and request.method in self.MUTATING_METHODS
            and user is not None
            and user.is_authenticated
            and (user.is_staff or user.is_superuser)
        ):
            match = getattr(request, 'resolver_match', None)
            forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
            ip = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')
            try:
                RegistroAuditoria.objects.create(
                    usuario=user,
                    metodo=request.method,
                    ruta=request.path[:500],
                    vista=(match.url_name if match else '') or '',
                    estado_http=response.status_code,
                    ip=ip or None,
                )
            except Exception:
                # La auditoría nunca debe interrumpir una operación administrativa.
                pass
        return response
