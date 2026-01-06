"""
ASGI config for bcp_drp_api project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bcp_drp_api.settings')

application = get_asgi_application()
