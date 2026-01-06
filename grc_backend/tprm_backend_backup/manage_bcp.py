#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    try:
        from django.core.management import execute_from_command_line
        from django.conf import settings
        
        # If running server command, use the port from settings
        if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
            # Check if port is already specified
            if len(sys.argv) == 2:  # Only 'runserver' command
                port = getattr(settings, 'DEFAULT_PORT', '5005')
                sys.argv.append(f'0.0.0.0:{port}')
            elif len(sys.argv) == 3 and ':' not in sys.argv[2]:  # Only IP specified
                port = getattr(settings, 'DEFAULT_PORT', '5005')
                sys.argv[2] = f'{sys.argv[2]}:{port}'
                
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
