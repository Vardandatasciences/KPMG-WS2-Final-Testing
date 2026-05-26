"""
Lightweight middleware to identify API version from request URL.
Adds X-API-Version header to API responses.
"""


class APIVersionMiddleware:
    """
    Middleware that detects API version from request path and adds
    X-API-Version header to the response.
    
    Version detection:
    - /api/v1.0/       -> X-API-Version: v1.0
    - /api/v2.0/       -> X-API-Version: v2.0
    - /api/ (no version) -> X-API-Version: unversioned
    - Non-API routes    -> No header added
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only process API routes
        path = request.path
        if not path.startswith('/api/'):
            return response
        
        # Determine API version from path
        if path.startswith('/api/v1.0/'):
            version = 'v1.0'
        elif path.startswith('/api/v2.0/'):
            version = 'v2.0'
        elif path.startswith('/api/'):
            version = 'unversioned'
        else:
            return response
        
        # Add version header to response
        response['X-API-Version'] = version
        
        return response
