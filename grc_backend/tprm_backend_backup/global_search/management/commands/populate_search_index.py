from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps
from tprm_backend.global_search.models import SearchIndex
from tprm_backend.global_search.signals import (
    index_vendor_data,
    index_rfp_data,
    index_contract_data,
    index_sla_data,
    index_bcp_drp_data
)


class Command(BaseCommand):
    help = 'Populate the search index with data from all TPRM modules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing search index before populating',
        )
        parser.add_argument(
            '--module',
            type=str,
            help='Only populate specific module (vendor, rfp, contract, sla, bcp_drp)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing search index...')
            SearchIndex.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Search index cleared'))

        modules_to_populate = []
        if options['module']:
            modules_to_populate = [options['module']]
        else:
            modules_to_populate = ['vendor', 'rfp', 'contract', 'sla', 'bcp_drp']

        total_indexed = 0

        for module in modules_to_populate:
            try:
                count = self.populate_module(module)
                total_indexed += count
                self.stdout.write(
                    self.style.SUCCESS(f'Indexed {count} {module} records')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to index {module}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully indexed {total_indexed} total records')
        )

    def populate_module(self, module_name):
        """Populate search index for a specific module."""
        count = 0
        
        try:
            # Get the model for the module
            if module_name == 'vendor':
                model = apps.get_model('vendor', 'Vendor')
                for instance in model.objects.all():
                    index_vendor_data(instance)
                    count += 1
                    
            elif module_name == 'rfp':
                model = apps.get_model('rfp', 'RFP')
                for instance in model.objects.all():
                    index_rfp_data(instance)
                    count += 1
                    
            elif module_name == 'contract':
                model = apps.get_model('contract', 'Contract')
                for instance in model.objects.all():
                    index_contract_data(instance)
                    count += 1
                    
            elif module_name == 'sla':
                model = apps.get_model('sla', 'SLA')
                for instance in model.objects.all():
                    index_sla_data(instance)
                    count += 1
                    
            elif module_name == 'bcp_drp':
                model = apps.get_model('bcp_drp', 'BCPDRP')
                for instance in model.objects.all():
                    index_bcp_drp_data(instance)
                    count += 1
                    
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Module {module_name} not found or has no data: {str(e)}')
            )
            
        return count
