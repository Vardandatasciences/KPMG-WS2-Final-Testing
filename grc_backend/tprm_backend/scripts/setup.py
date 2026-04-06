#!/usr/bin/env python
"""
Django project setup script
Run this after installing requirements to set up the database
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_django():
    """Setup Django project"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mfa_project.settings')
    django.setup()

def run_migrations():
    """Run database migrations"""
    print("Running database migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    execute_from_command_line(['manage.py', 'migrate'])
    print("✅ Migrations completed!")

def create_superuser():
    """Create superuser if it doesn't exist (password from DJANGO_SUPERUSER_PASSWORD)."""
    from django.contrib.auth.models import User

    if User.objects.filter(is_superuser=True).exists():
        print("✅ Superuser already exists!")
        return

    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "").strip()
    if not password:
        print(
            "⚠️ Skipping superuser creation: set DJANGO_SUPERUSER_PASSWORD in the environment."
        )
        return

    print("Creating superuser...")
    User.objects.create_superuser(
        username=os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin"),
        email=os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com"),
        password=password,
    )
    print("✅ Superuser created (username from DJANGO_SUPERUSER_USERNAME or admin).")

def collect_static():
    """Collect static files"""
    print("Collecting static files...")
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    print("✅ Static files collected!")

def main():
    """Main setup function"""
    print("🚀 Setting up Django project...")
    
    try:
        setup_django()
        run_migrations()
        create_superuser()
        collect_static()
        print("\n🎉 Setup completed successfully!")
        print("You can now run: python manage.py runserver")
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
