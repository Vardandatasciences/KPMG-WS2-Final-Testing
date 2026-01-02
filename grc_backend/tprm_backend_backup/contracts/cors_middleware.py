"""
Custom CORS middleware to handle cross-origin requests
"""

from django.http import HttpResponse

class CustomCORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Handle preflight requests
        if request.method == 'OPTIONS':
            response = HttpResponse()
            response['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
            return response

        response = self.get_response(request)

        # Add CORS headers to all responses
        origin = request.headers.get('Origin')
        if origin and ('localhost' in origin or '127.0.0.1' in origin):
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'

        return response
