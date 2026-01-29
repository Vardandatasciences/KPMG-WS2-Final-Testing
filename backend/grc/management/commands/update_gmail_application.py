from django.core.management.base import BaseCommand
from django.utils import timezone
import json
from grc.models import ExternalApplication


class Command(BaseCommand):
    help = 'Update or create Gmail application configuration in external_applications table'

    def handle(self, *args, **options):
        try:
            # Gmail application configuration
            gmail_config = {
                'name': 'Gmail',
                'category': 'Communication',
                'type': 'OAuth',
                'description': 'Gmail is Google\'s cloud-based email service designed to meet the communication needs of businesses and organizations. It provides secure email communication, calendar integration, and file sharing capabilities.',
                'icon_class': 'fas fa-envelope',
                'version': 'v1.0.0',
                'status': 'connected',
                'is_active': True,
                'configuration': json.dumps({
                    'oauth2': {
                        'client_id': '485924947413-c0agg3va7u43ahf1cll50ekas5aba5a6.apps.googleusercontent.com',
                        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                        'token_uri': 'https://oauth2.googleapis.com/token',
                        'redirect_uri': 'http://localhost:8000/api/gmail/oauth-callback/',
                        'scopes': [
                            'openid',
                            'https://www.googleapis.com/auth/gmail.readonly',
                            'https://www.googleapis.com/auth/calendar.readonly',
                            'https://www.googleapis.com/auth/userinfo.profile',
                            'https://www.googleapis.com/auth/userinfo.email'
                        ]
                    },
                    'api_endpoints': {
                        'gmail_api': 'https://gmail.googleapis.com/gmail/v1',
                        'calendar_api': 'https://www.googleapis.com/calendar/v3',
                        'user_info_api': 'https://www.googleapis.com/oauth2/v2/userinfo'
                    },
                    'features': {
                        'email_reading': True,
                        'calendar_integration': True,
                        'attachment_download': True,
                        'real_time_sync': True,
                        'user_authentication': True
                    }
                }),
                'api_endpoint': 'https://gmail.googleapis.com/gmail/v1',
                'oauth_url': 'https://accounts.google.com/o/oauth2/auth',
                'features': json.dumps({
                    'email_reading': True,
                    'calendar_integration': True,
                    'attachment_download': True,
                    'real_time_sync': True,
                    'user_authentication': True,
                    'supported_formats': ['pdf', 'docx', 'xlsx', 'png', 'jpg', 'jpeg', 'gif'],
                    'max_attachment_size': '25MB',
                    'rate_limits': {
                        'requests_per_minute': 1000,
                        'quota_per_day': 1000000
                    }
                }),
                'last_sync': timezone.now(),
                'created_at': timezone.now(),
                'updated_at': timezone.now()
            }

            # Get or create Gmail application
            gmail_app, created = ExternalApplication.objects.get_or_create(
                name='Gmail',
                defaults=gmail_config
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS('✅ Successfully created Gmail application configuration')
                )
            else:
                # Update existing Gmail application
                for key, value in gmail_config.items():
                    if key != 'name':  # Don't update the name
                        setattr(gmail_app, key, value)
                
                gmail_app.save()
                self.stdout.write(
                    self.style.SUCCESS('✅ Successfully updated Gmail application configuration')
                )

            self.stdout.write(
                self.style.SUCCESS(f'Gmail Application ID: {gmail_app.id}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Status: {gmail_app.status}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'API Endpoint: {gmail_app.api_endpoint}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'OAuth URL: {gmail_app.oauth_url}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error updating Gmail application: {str(e)}')
            )
