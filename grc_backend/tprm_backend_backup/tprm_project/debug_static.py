from django.http import HttpResponse, Http404
from django.conf import settings
import os

def debug_static_file(request, filename):
    """Debug function to check static file serving"""
    try:
        # Try to find the file in staticfiles directory
        file_path = os.path.join(settings.STATIC_ROOT, filename)
        
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
            return HttpResponse(f"File not found: {file_path}", status=404)
    
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
