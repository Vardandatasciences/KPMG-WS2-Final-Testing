"""
Management command to add dummy users for testing
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = 'Add dummy users to the users table for testing'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                # Check if users already exist
                cursor.execute("SELECT COUNT(*) FROM users")
                existing_count = cursor.fetchone()[0]
                
                if existing_count > 0:
                    self.stdout.write(
                        self.style.WARNING(f'Users table already has {existing_count} users. Skipping...')
                    )
                    return
                
                # Add dummy users
                dummy_users = [
                    ('John Admin', 'john.admin@company.com', 'admin123'),
                    ('Jane Manager', 'jane.manager@company.com', 'manager123'),
                    ('Bob Employee', 'bob.employee@company.com', 'employee123'),
                    ('Alice Finance', 'alice.finance@company.com', 'finance123'),
                    ('Charlie IT', 'charlie.it@company.com', 'it123'),
                    ('Diana HR', 'diana.hr@company.com', 'hr123'),
                    ('Eve Operations', 'eve.operations@company.com', 'ops123'),
                    ('Frank Security', 'frank.security@company.com', 'security123'),
                    ('Grace Legal', 'grace.legal@company.com', 'legal123'),
                    ('Henry Compliance', 'henry.compliance@company.com', 'compliance123')
                ]
                
                for user_name, email, password in dummy_users:
                    cursor.execute("""
                        INSERT INTO users (UserName, Email, Password, CreatedAt, UpdatedAt) 
                        VALUES (%s, %s, %s, %s, %s)
                    """, [user_name, email, password, timezone.now(), timezone.now()])
                
                connection.commit()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully added {len(dummy_users)} dummy users to the database')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error adding dummy users: {str(e)}')
            )
