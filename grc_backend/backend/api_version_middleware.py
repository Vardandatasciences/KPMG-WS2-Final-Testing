"""
API Version Middleware

Lightweight middleware to identify API version from request URL
and return it in the X-API-Version response header.
"""


class APIVersionMiddleware:
    """
    Middleware that detects API version from URL path and adds
    X-API-Version header to the response.

    Rules:
    - /api/v1.0/*       -> X-API-Version: v1.0
    - /api/v2.0/*       -> X-API-Version: v2.0
    - /api/* (no ver)   -> X-API-Version: unversioned
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
        version = self._detect_version(path)
        if version:
            response['X-API-Version'] = version

        return response

    def _detect_version(self, path):
        """Detect API version from URL path."""
        # Check for v1.0
        if path.startswith('/api/v1.0/'):
            return 'v1.0'

        # Check for v2.0
        if path.startswith('/api/v2.0/'):
            return 'v2.0'

        # Any other /api/ path is unversioned
        if path.startswith('/api/'):
            return 'unversioned'

        return None
