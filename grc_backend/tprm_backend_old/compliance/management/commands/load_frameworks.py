"""
Management command to load sample frameworks data.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from tprm_backend.compliance.models import Framework


class Command(BaseCommand):
    help = 'Load sample frameworks data'

    def handle(self, *args, **options):
        frameworks_data = [
            {
                'FrameworkName': 'ISO 27001',
                'CurrentVersion': 2.0,
                'FrameworkDescription': 'Information security management system standard that provides a framework for managing and protecting information assets.',
                'EffectiveDate': '2022-10-01',
                'CreatedByName': 'System Administrator',
                'CreatedByDate': '2022-09-01',
                'Category': 'Security',
                'DocURL': 'https://www.iso.org/isoiec-27001-information-security.html',
                'Identifier': 'ISO/IEC 27001:2022',
                'StartDate': '2022-10-01',
                'EndDate': None,
                'Status': 'Active',
                'ActiveInactive': 'Active',
                'Reviewer': 'Security Team',
                'InternalExternal': 'External'
            },
            {
                'FrameworkName': 'SOC 2',
                'CurrentVersion': 1.0,
                'FrameworkDescription': 'Service Organization Control 2 for security, availability, processing integrity, confidentiality, and privacy.',
                'EffectiveDate': '2023-01-01',
                'CreatedByName': 'System Administrator',
                'CreatedByDate': '2022-12-01',
                'Category': 'Compliance',
                'DocURL': 'https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/aicpasoc2report',
                'Identifier': 'SOC 2 Type II',
                'StartDate': '2023-01-01',
                'EndDate': None,
                'Status': 'Active',
                'ActiveInactive': 'Active',
                'Reviewer': 'Compliance Team',
                'InternalExternal': 'External'
            },
            {
                'FrameworkName': 'GDPR',
                'CurrentVersion': 1.0,
                'FrameworkDescription': 'General Data Protection Regulation for data privacy and protection of personal data.',
                'EffectiveDate': '2018-05-25',
                'CreatedByName': 'System Administrator',
                'CreatedByDate': '2018-04-01',
                'Category': 'Privacy',
                'DocURL': 'https://gdpr.eu/',
                'Identifier': 'EU GDPR',
                'StartDate': '2018-05-25',
                'EndDate': None,
                'Status': 'Active',
                'ActiveInactive': 'Active',
                'Reviewer': 'Privacy Team',
                'InternalExternal': 'External'
            },
            {
                'FrameworkName': 'NIST Cybersecurity Framework',
                'CurrentVersion': 1.1,
                'FrameworkDescription': 'A framework for improving critical infrastructure cybersecurity.',
                'EffectiveDate': '2018-04-16',
                'CreatedByName': 'System Administrator',
                'CreatedByDate': '2018-03-01',
                'Category': 'Security',
                'DocURL': 'https://www.nist.gov/cyberframework',
                'Identifier': 'NIST CSF 1.1',
                'StartDate': '2018-04-16',
                'EndDate': None,
                'Status': 'Active',
                'ActiveInactive': 'Active',
                'Reviewer': 'Security Team',
                'InternalExternal': 'External'
            },
            {
                'FrameworkName': 'PCI DSS',
                'CurrentVersion': 4.0,
                'FrameworkDescription': 'Payment Card Industry Data Security Standard for organizations that handle credit card information.',
                'EffectiveDate': '2024-03-31',
                'CreatedByName': 'System Administrator',
                'CreatedByDate': '2024-02-01',
                'Category': 'Compliance',
                'DocURL': 'https://www.pcisecuritystandards.org/',
                'Identifier': 'PCI DSS v4.0',
                'StartDate': '2024-03-31',
                'EndDate': None,
                'Status': 'Active',
                'ActiveInactive': 'Active',
                'Reviewer': 'Compliance Team',
                'InternalExternal': 'External'
            }
        ]

        created_count = 0
        for framework_data in frameworks_data:
            framework, created = Framework.objects.get_or_create(
                FrameworkName=framework_data['FrameworkName'],
                defaults=framework_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created framework: {framework.FrameworkName}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Framework already exists: {framework.FrameworkName}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully loaded {created_count} new frameworks')
        )
