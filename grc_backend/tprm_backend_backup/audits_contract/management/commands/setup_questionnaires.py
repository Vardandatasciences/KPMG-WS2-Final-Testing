from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    help = 'Setup questionnaires in the database'

    def handle(self, *args, **options):
        self.stdout.write('Setting up questionnaires...')
        
        try:
            with connections['default'].cursor() as cursor:
                # Check if table exists
                cursor.execute("SHOW TABLES LIKE 'contract_static_questionnaires'")
                table_exists = cursor.fetchone()
                
                if not table_exists:
                    self.stdout.write('Creating contract_static_questionnaires table...')
                    create_table_sql = """
                        CREATE TABLE contract_static_questionnaires (
                            question_id INT AUTO_INCREMENT PRIMARY KEY,
                            term_id VARCHAR(255),
                            question_text TEXT,
                            question_type VARCHAR(20),
                            is_required BOOLEAN DEFAULT FALSE,
                            scoring_weightings DECIMAL(5,2) DEFAULT 10.00,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """
                    cursor.execute(create_table_sql)
                    self.stdout.write('✓ Table created successfully')
                
                # Clear existing data
                cursor.execute("DELETE FROM contract_static_questionnaires")
                
                # Insert sample data
                sample_data = [
                    (1, '1', 'Is the service provider meeting the agreed response time?', 'boolean', 1, 15.00),
                    (2, '1', 'What is the average response time in hours?', 'number', 1, 10.00),
                    (3, '1', 'Describe the service quality observed', 'text', 1, 20.00),
                    (4, '2', 'Is data encryption implemented according to contract requirements?', 'boolean', 1, 25.00),
                    (5, '2', 'What type of encryption is being used?', 'multiple_choice', 0, 10.00),
                    (6, '2', 'Describe the data security measures in place', 'text', 1, 15.00),
                    (7, '3', 'Is the system uptime meeting the agreed percentage?', 'boolean', 1, 20.00),
                    (8, '3', 'What is the actual uptime percentage?', 'number', 1, 15.00),
                    (9, '3', 'Describe any performance issues encountered', 'text', 0, 10.00),
                ]
                
                insert_sql = """
                    INSERT INTO contract_static_questionnaires 
                    (question_id, term_id, question_text, question_type, is_required, scoring_weightings, created_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """
                
                for data in sample_data:
                    cursor.execute(insert_sql, data)
                
                self.stdout.write(f'✓ Inserted {len(sample_data)} questionnaires')
                
                # Verify insertion
                cursor.execute("SELECT COUNT(*) FROM contract_static_questionnaires")
                count = cursor.fetchone()[0]
                self.stdout.write(f'✓ Total questionnaires in database: {count}')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up questionnaires: {e}')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS('Questionnaires setup completed successfully!')
        )
