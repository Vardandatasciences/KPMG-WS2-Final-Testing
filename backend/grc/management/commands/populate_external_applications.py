from django.core.management.base import BaseCommand
from django.utils import timezone
from grc.models import ExternalApplication


class Command(BaseCommand):
    help = 'Populate external applications table with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Populating external applications...')

        # Sample external applications data
        applications_data = [
            {
                'name': 'Microsoft Azure',
                'category': 'Cloud Platform',
                'type': 'Cloud Service',
                'description': 'Connect to Azure Active Directory and Azure services for identity management and cloud resource monitoring.',
                'icon_class': 'fab fa-microsoft',
                'version': 'v2.1.0',
                'status': 'disconnected',
                'api_endpoint': 'https://graph.microsoft.com/v1.0',
                'oauth_url': 'https://login.microsoftonline.com/oauth2/v2.0/authorize',
                'features': [
                    'Active Directory integration',
                    'Cloud resource monitoring',
                    'Identity management',
                    'Compliance reporting'
                ]
            },
            {
                'name': 'AWS',
                'category': 'Cloud Platform',
                'type': 'Cloud Service',
                'description': 'Integrate with Amazon Web Services for cloud security monitoring and compliance management.',
                'icon_class': 'fab fa-aws',
                'version': 'v1.8.2',
                'status': 'disconnected',
                'api_endpoint': 'https://aws.amazon.com/api',
                'oauth_url': 'https://aws.amazon.com/oauth',
                'features': [
                    'CloudTrail integration',
                    'Config Rules monitoring',
                    'Security Hub integration',
                    'Cost optimization'
                ]
            },
            {
                'name': 'ServiceNow',
                'category': 'ITSM',
                'type': 'Service Management',
                'description': 'Connect to ServiceNow for incident management, change management, and IT service operations.',
                'icon_class': 'fas fa-cogs',
                'version': 'v3.0.1',
                'status': 'disconnected',
                'api_endpoint': 'https://your-instance.service-now.com/api/now',
                'oauth_url': 'https://your-instance.service-now.com/oauth_auth.do',
                'features': [
                    'Incident management',
                    'Change management',
                    'Asset management',
                    'Service catalog'
                ]
            },
            {
                'name': 'Splunk',
                'category': 'SIEM',
                'type': 'Security Monitoring',
                'description': 'Integrate with Splunk for security information and event management, log analysis, and threat detection.',
                'icon_class': 'fas fa-shield-alt',
                'version': 'v2.5.0',
                'status': 'disconnected',
                'api_endpoint': 'https://your-splunk-instance:8089/services',
                'oauth_url': 'https://your-splunk-instance:8089/services/auth/login',
                'features': [
                    'Log analysis',
                    'Threat detection',
                    'Security monitoring',
                    'Compliance reporting'
                ]
            },
            {
                'name': 'Salesforce',
                'category': 'CRM',
                'type': 'Customer Management',
                'description': 'Connect to Salesforce for customer relationship management and business process automation.',
                'icon_class': 'fab fa-salesforce',
                'version': 'v1.9.3',
                'status': 'disconnected',
                'api_endpoint': 'https://your-instance.salesforce.com/services/data/v58.0',
                'oauth_url': 'https://your-instance.salesforce.com/services/oauth2/authorize',
                'features': [
                    'Customer data management',
                    'Sales pipeline tracking',
                    'Marketing automation',
                    'Analytics and reporting'
                ]
            },
            {
                'name': 'Jira',
                'category': 'Project Management',
                'type': 'Issue Tracking',
                'description': 'Integrate with Jira for project management, issue tracking, and agile development workflows.',
                'icon_class': 'fab fa-jira',
                'version': 'v2.2.1',
                'status': 'disconnected',
                'api_endpoint': 'http://localhost:5000/jira-projects',
                'oauth_url': 'http://localhost:5000/oauth',
                'features': [
                    'Issue tracking',
                    'Project management',
                    'Agile workflows',
                    'Time tracking'
                ]
            }
        ]

        created_count = 0
        updated_count = 0

        for app_data in applications_data:
            app, created = ExternalApplication.objects.update_or_create(
                name=app_data['name'],
                defaults=app_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created: {app.name}')
            else:
                updated_count += 1
                self.stdout.write(f'Updated: {app.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated external applications. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )
