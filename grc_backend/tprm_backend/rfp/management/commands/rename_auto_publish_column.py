"""
Django management command to rename auto_publish column to auto_approve
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Rename auto_publish column to auto_approve in rfps table'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                # Get database name
                cursor.execute("SELECT DATABASE()")
                db_name = cursor.fetchone()[0]
                self.stdout.write(f'📊 Database: {db_name}')
                
                # List all columns in rfps table
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, COLUMN_DEFAULT, IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'rfps'
                    ORDER BY COLUMN_NAME
                """)
                columns = cursor.fetchall()
                self.stdout.write(f'\n📋 Columns in rfps table:')
                for col in columns:
                    self.stdout.write(f'   - {col[0]} ({col[1]})')
                
                # Check if auto_publish column exists
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'rfps' 
                    AND COLUMN_NAME = 'auto_publish'
                """)
                auto_publish_exists = cursor.fetchone()[0] > 0
                
                # Check if auto_approve column exists
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'rfps' 
                    AND COLUMN_NAME = 'auto_approve'
                """)
                auto_approve_exists = cursor.fetchone()[0] > 0
                
                # Check if auto_approved column exists (the actual current name)
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'rfps' 
                    AND COLUMN_NAME = 'auto_approved'
                """)
                auto_approved_exists = cursor.fetchone()[0] > 0
                
                self.stdout.write(f'\n🔍 auto_publish exists: {auto_publish_exists}')
                self.stdout.write(f'🔍 auto_approved exists: {auto_approved_exists}')
                self.stdout.write(f'🔍 auto_approve exists: {auto_approve_exists}\n')
                
                if auto_approved_exists and not auto_approve_exists:
                    # Rename auto_approved to auto_approve
                    cursor.execute("ALTER TABLE rfps CHANGE COLUMN auto_approved auto_approve BOOLEAN DEFAULT FALSE")
                    self.stdout.write(self.style.SUCCESS('✅ Successfully renamed auto_approved to auto_approve'))
                elif auto_publish_exists and not auto_approve_exists:
                    # Rename auto_publish to auto_approve
                    cursor.execute("ALTER TABLE rfps CHANGE COLUMN auto_publish auto_approve BOOLEAN DEFAULT FALSE")
                    self.stdout.write(self.style.SUCCESS('✅ Successfully renamed auto_publish to auto_approve'))
                elif not auto_publish_exists and not auto_approved_exists and auto_approve_exists:
                    self.stdout.write(self.style.WARNING('⚠️  Column already renamed to auto_approve'))
                elif auto_publish_exists and auto_approve_exists:
                    # Both exist - drop auto_publish
                    cursor.execute("ALTER TABLE rfps DROP COLUMN auto_publish")
                    self.stdout.write(self.style.SUCCESS('✅ Removed duplicate auto_publish column'))
                elif auto_approved_exists and auto_approve_exists:
                    # Both exist - drop auto_approved
                    cursor.execute("ALTER TABLE rfps DROP COLUMN auto_approved")
                    self.stdout.write(self.style.SUCCESS('✅ Removed duplicate auto_approved column'))
                else:
                    self.stdout.write(self.style.ERROR('❌ Column not found. Adding auto_approve column...'))
                    cursor.execute("ALTER TABLE rfps ADD COLUMN auto_approve BOOLEAN DEFAULT FALSE")
                    self.stdout.write(self.style.SUCCESS('✅ Added auto_approve column'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
                import traceback
                self.stdout.write(traceback.format_exc())
                raise

