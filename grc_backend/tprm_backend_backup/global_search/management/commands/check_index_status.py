from django.core.management.base import BaseCommand
from django.db import connection
from tprm_backend.global_search.models import SearchIndex


class Command(BaseCommand):
    help = 'Check the status of the search index and show statistics'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Checking Search Index Status...\n')
        
        # Get total count
        total_count = SearchIndex.objects.count()
        self.stdout.write(f'Total indexed records: {total_count}')
        
        if total_count == 0:
            self.stdout.write(self.style.WARNING('⚠️  No records found in search index!'))
            self.stdout.write('Run: python manage.py populate_search_index to index your data')
            return
        
        # Get counts by entity type
        self.stdout.write('\n📊 Records by Entity Type:')
        for entity_type in ['vendor', 'rfp', 'contract', 'sla', 'bcp_drp']:
            count = SearchIndex.objects.filter(entity_type=entity_type).count()
            self.stdout.write(f'  {entity_type.capitalize()}: {count}')
        
        # Get recent updates
        self.stdout.write('\n🕒 Recent Updates:')
        recent = SearchIndex.objects.order_by('-updated_at')[:5]
        for record in recent:
            self.stdout.write(f'  {record.entity_type}:{record.entity_id} - {record.title} (Updated: {record.updated_at})')
        
        # Check for potential issues
        self.stdout.write('\n🔧 Index Health Check:')
        
        # Check for empty titles
        empty_titles = SearchIndex.objects.filter(title='').count()
        if empty_titles > 0:
            self.stdout.write(self.style.WARNING(f'  ⚠️  {empty_titles} records with empty titles'))
        else:
            self.stdout.write('  ✅ All records have titles')
        
        # Check for duplicate entity entries
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT entity_type, entity_id, COUNT(*) as count
                FROM search_index
                GROUP BY entity_type, entity_id
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            
        if duplicates:
            self.stdout.write(self.style.WARNING(f'  ⚠️  {len(duplicates)} duplicate entity entries found'))
        else:
            self.stdout.write('  ✅ No duplicate entries found')
        
        self.stdout.write('\n✅ Search index status check completed!')

