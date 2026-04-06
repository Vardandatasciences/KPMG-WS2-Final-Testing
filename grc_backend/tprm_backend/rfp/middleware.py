from django.conf import settings


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        # Add Content-Security-Policy header
        csp_directives = [
            "default-src 'self'",
            "img-src 'self' data:",
            "style-src 'self'",
            "script-src 'self'",
            "connect-src 'self'",
            "font-src 'self' data:",
            "object-src 'none'",
            "base-uri 'none'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
        response['Content-Security-Policy'] = '; '.join(csp_directives)

        if not settings.DEBUG:
            secs = int(getattr(settings, 'SECURE_HSTS_SECONDS', 0) or 0)
            if secs > 0:
                h = [f'max-age={secs}']
                if getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False):
                    h.append('includeSubDomains')
                if getattr(settings, 'SECURE_HSTS_PRELOAD', False):
                    h.append('preload')
                response['Strict-Transport-Security'] = '; '.join(h)
        
        return response
