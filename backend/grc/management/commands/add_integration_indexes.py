from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Add database indexes for IntegrationDataList to improve query performance'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                # Add composite index for time and created_at for better sorting performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_integration_time_created 
                    ON integration_data_list (time DESC, created_at DESC)
                """)
                
                # Add index for source field if not exists
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_integration_source 
                    ON integration_data_list (source)
                """)
                
                # Add index for username field if not exists  
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_integration_username 
                    ON integration_data_list (username)
                """)
                
                self.stdout.write(
                    self.style.SUCCESS('Successfully added database indexes for IntegrationDataList')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error adding indexes: {str(e)}')
            )
            logger.error(f'Error adding IntegrationDataList indexes: {str(e)}')
