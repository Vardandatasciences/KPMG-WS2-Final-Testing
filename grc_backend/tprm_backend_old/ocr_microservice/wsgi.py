"""
WSGI config for ocr_microservice project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ocr_microservice.settings')

application = get_wsgi_application()
