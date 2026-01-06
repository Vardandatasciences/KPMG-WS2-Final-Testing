from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import json


class Command(BaseCommand):
    help = 'Create test data for all TPRM modules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating test data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_existing_data()

        self.stdout.write('Creating test data...')
        
        # Create test data for each module
        self.create_vendor_data()
        self.create_rfp_data()
        self.create_contract_data()
        self.create_sla_data()
        self.create_bcp_drp_data()
        
        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))

    def clear_existing_data(self):
        """Clear existing data from all modules."""
        from django.apps import apps
        
        models_to_clear = [
            ('vendor', 'Vendor'),
            ('rfp', 'RFP'),
            ('contract', 'Contract'),
            ('sla', 'SLA'),
            ('bcp_drp', 'BCPDRP'),
        ]
        
        for app_name, model_name in models_to_clear:
            try:
                model = apps.get_model(app_name, model_name)
                model.objects.all().delete()
                self.stdout.write(f'Cleared {app_name}.{model_name}')
            except Exception as e:
                self.stdout.write(f'Could not clear {app_name}.{model_name}: {e}')

    def create_vendor_data(self):
        """Create test vendor data."""
        try:
            from vendor.models import Vendor
            
            vendors = [
                {
                    'name': 'Acme Corporation',
                    'description': 'Leading technology vendor providing cloud services and consulting',
                    'category': 'Technology',
                    'status': 'active',
                    'contact_email': 'contact@acme.com',
                    'risk_level': 'medium'
                },
                {
                    'name': 'Tech Solutions Inc',
                    'description': 'IT infrastructure and support services provider',
                    'category': 'Technology',
                    'status': 'active',
                    'contact_email': 'info@techsolutions.com',
                    'risk_level': 'low'
                },
                {
                    'name': 'Global Consulting Group',
                    'description': 'Management consulting and advisory services',
                    'category': 'Consulting',
                    'status': 'active',
                    'contact_email': 'hello@globalconsulting.com',
                    'risk_level': 'high'
                }
            ]
            
            for vendor_data in vendors:
                Vendor.objects.get_or_create(
                    name=vendor_data['name'],
                    defaults=vendor_data
                )
            
            self.stdout.write('Created vendor test data')
            
        except Exception as e:
            self.stdout.write(f'Could not create vendor data: {e}')

    def create_rfp_data(self):
        """Create test RFP data."""
        try:
            from rfp.models import RFP
            
            rfps = [
                {
                    'title': 'Cloud Migration Services RFP',
                    'description': 'Request for proposal for cloud migration and infrastructure services',
                    'status': 'published',
                    'category': 'technology',
                    'risk_level': 'medium',
                    'deadline': date.today() + timedelta(days=30),
                    'budget': '500000'
                },
                {
                    'title': 'Cybersecurity Assessment RFP',
                    'description': 'Security assessment and penetration testing services',
                    'status': 'draft',
                    'category': 'technology',
                    'risk_level': 'high',
                    'deadline': date.today() + timedelta(days=45),
                    'budget': '200000'
                }
            ]
            
            for rfp_data in rfps:
                RFP.objects.get_or_create(
                    title=rfp_data['title'],
                    defaults=rfp_data
                )
            
            self.stdout.write('Created RFP test data')
            
        except Exception as e:
            self.stdout.write(f'Could not create RFP data: {e}')

    def create_contract_data(self):
        """Create test contract data."""
        try:
            from contract.models import Contract
            
            contracts = [
                {
                    'title': 'Acme Cloud Services Agreement',
                    'description': 'Master service agreement for cloud hosting and support services',
                    'status': 'active',
                    'category': 'technology',
                    'risk_level': 'medium',
                    'vendor_name': 'Acme Corporation',
                    'start_date': date.today() - timedelta(days=365),
                    'end_date': date.today() + timedelta(days=365),
                    'value': '1000000'
                },
                {
                    'title': 'Tech Solutions Support Contract',
                    'description': 'IT support and maintenance contract',
                    'status': 'active',
                    'category': 'services',
                    'risk_level': 'low',
                    'vendor_name': 'Tech Solutions Inc',
                    'start_date': date.today() - timedelta(days=180),
                    'end_date': date.today() + timedelta(days=180),
                    'value': '500000'
                }
            ]
            
            for contract_data in contracts:
                Contract.objects.get_or_create(
                    title=contract_data['title'],
                    defaults=contract_data
                )
            
            self.stdout.write('Created contract test data')
            
        except Exception as e:
            self.stdout.write(f'Could not create contract data: {e}')

    def create_sla_data(self):
        """Create test SLA data."""
        try:
            from sla.models import SLA
            
            slas = [
                {
                    'title': 'Acme Cloud Uptime SLA',
                    'description': 'Service level agreement for 99.9% uptime guarantee',
                    'status': 'active',
                    'service_type': 'cloud_services',
                    'category': 'technology',
                    'risk_level': 'medium',
                    'vendor_name': 'Acme Corporation',
                    'uptime_target': '99.9%'
                },
                {
                    'title': 'Tech Solutions Support SLA',
                    'description': 'IT support response time and resolution SLA',
                    'status': 'active',
                    'service_type': 'it_support',
                    'category': 'services',
                    'risk_level': 'low',
                    'vendor_name': 'Tech Solutions Inc',
                    'uptime_target': '4-hour response'
                }
            ]
            
            for sla_data in slas:
                SLA.objects.get_or_create(
                    title=sla_data['title'],
                    defaults=sla_data
                )
            
            self.stdout.write('Created SLA test data')
            
        except Exception as e:
            self.stdout.write(f'Could not create SLA data: {e}')

    def create_bcp_drp_data(self):
        """Create test BCP/DRP data."""
        try:
            from bcp_drp.models import BCPDRP
            
            plans = [
                {
                    'title': 'Acme Disaster Recovery Plan',
                    'description': 'Comprehensive disaster recovery and business continuity plan',
                    'plan_type': 'combined',
                    'status': 'active',
                    'category': 'technology',
                    'risk_level': 'high',
                    'vendor_name': 'Acme Corporation',
                    'effective_date': date.today() - timedelta(days=30),
                    'review_date': date.today() + timedelta(days=335),
                    'rto': '4 hours',
                    'rpo': '1 hour',
                    'mto': '8 hours',
                    'scope': 'All critical business functions and IT systems',
                    'critical_functions': json.dumps(['Customer portal', 'Payment processing', 'Data analytics']),
                    'recovery_procedures': 'Detailed step-by-step recovery procedures for each system'
                },
                {
                    'title': 'Tech Solutions Business Continuity Plan',
                    'description': 'Business continuity plan for IT support services',
                    'plan_type': 'bcp',
                    'status': 'active',
                    'category': 'services',
                    'risk_level': 'medium',
                    'vendor_name': 'Tech Solutions Inc',
                    'effective_date': date.today() - timedelta(days=60),
                    'review_date': date.today() + timedelta(days=305),
                    'rto': '8 hours',
                    'rpo': '4 hours',
                    'mto': '24 hours',
                    'scope': 'IT support and maintenance services',
                    'critical_functions': json.dumps(['Help desk', 'System monitoring', 'Backup services']),
                    'recovery_procedures': 'IT support recovery and failover procedures'
                }
            ]
            
            for plan_data in plans:
                BCPDRP.objects.get_or_create(
                    title=plan_data['title'],
                    defaults=plan_data
                )
            
            self.stdout.write('Created BCP/DRP test data')
            
        except Exception as e:
            self.stdout.write(f'Could not create BCP/DRP data: {e}')
