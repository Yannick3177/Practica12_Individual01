import logging
import time

logger = logging.getLogger('core')


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.start_time = time.time()
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'
        logger.info(
            f"[REQUEST] {request.method} {request.get_full_path()} | User: {user} | IP: {self.get_client_ip(request)}"
        )

        response = self.get_response(request)

        duration = round((time.time() - request.start_time) * 1000, 2)
        logger.info(
            f"[RESPONSE] {request.method} {request.get_full_path()} | Status: {response.status_code} | Time: {duration}ms"
        )
        
        response['X-Frame-Options'] = 'DENY'
        response['X-Content-Type-Options'] = 'nosniff'
        response['Content-Security-Policy'] = "default-src 'self'"
        
        return response

    @staticmethod
    def get_client_ip(request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')