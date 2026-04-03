from django.http import HttpResponse, Http404
from django.conf import settings
import os

def debug_static_file(request, filename):
    """Debug function to check static file serving"""
    try:
        from grc.utils.safe_paths import safe_join

        # Try to find the file in staticfiles directory (defensive against traversal)
        file_path = safe_join(settings.STATIC_ROOT, filename)
        
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Determine content type
            if filename.endswith('.js'):
                content_type = 'application/javascript'
            elif filename.endswith('.css'):
                content_type = 'text/css'
            else:
                content_type = 'application/octet-stream'
            
            response = HttpResponse(content, content_type=content_type)
            response['Content-Length'] = len(content)
            return response
        else:
            # Avoid disclosing full server path on missing/unsafe targets.
            return HttpResponse("File not found", status=404)
    
    except Exception as e:
        return HttpResponse("Error", status=500)
