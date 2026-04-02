"""
Custom CORS middleware to handle cross-origin requests
"""

class CustomCORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # CORS is centrally handled by django-cors-headers settings.
        # Keep this middleware as a no-op to avoid unsafe origin reflection.
        return self.get_response(request)
