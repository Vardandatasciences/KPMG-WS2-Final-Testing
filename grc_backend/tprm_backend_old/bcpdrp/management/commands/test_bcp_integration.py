"""
Management command to test BCP/DRP integration
"""
from django.core.management.base import BaseCommand
from django.db import connections
from django.conf import settings


class Command(BaseCommand):
    help = 'Test BCP/DRP integration'

    def handle(self, *args, **options):
        self.stdout.write('Testing BCP/DRP integration...')
        
        # Test database connections
        try:
            # Test default database (tprm_integration)
            default_conn = connections['default']
            with default_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(
                    self.style.SUCCESS('✓ Default database (tprm_integration) connection successful')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Default database connection failed: {e}')
            )
        
        # Test installed apps
        bcpdrp_installed = 'bcpdrp' in settings.INSTALLED_APPS
        risk_analysis_installed = 'risk_analysis' in settings.INSTALLED_APPS
        
        if bcpdrp_installed:
            self.stdout.write(
                self.style.SUCCESS('✓ bcpdrp app is installed')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ bcpdrp app is not installed')
            )
        
        if risk_analysis_installed:
            self.stdout.write(
                self.style.SUCCESS('✓ risk_analysis app is installed')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ risk_analysis app is not installed')
            )
        
        # Test URL patterns
        from django.urls import get_resolver
        resolver = get_resolver()
        bcpdrp_urls = any('bcpdrp' in str(pattern) for pattern in resolver.url_patterns)
        risk_analysis_urls = any('risk-analysis' in str(pattern) for pattern in resolver.url_patterns)
        
        if bcpdrp_urls:
            self.stdout.write(
                self.style.SUCCESS('✓ BCP/DRP URLs are configured')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ BCP/DRP URLs are not configured')
            )
        
        if risk_analysis_urls:
            self.stdout.write(
                self.style.SUCCESS('✓ Risk Analysis URLs are configured')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ Risk Analysis URLs are not configured')
            )
        
        self.stdout.write(
            self.style.SUCCESS('\nBCP/DRP integration test completed!')
        )
