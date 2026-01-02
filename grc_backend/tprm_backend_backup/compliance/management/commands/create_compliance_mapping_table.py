from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Create compliance_mapping table'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Create the compliance_mapping table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_mapping (
                    mapping_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    sla_id BIGINT NOT NULL,
                    framework_id INT NOT NULL,
                    compliance_status VARCHAR(50) DEFAULT 'Compliant',
                    compliance_score DECIMAL(5, 2) DEFAULT 100.00,
                    last_audited DATE,
                    next_audit_due DATE,
                    assigned_auditor VARCHAR(255),
                    audit_frequency ENUM('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY') DEFAULT 'MONTHLY',
                    compliance_version VARCHAR(50) NOT NULL,
                    compliance_description TEXT,
                    UNIQUE KEY unique_sla_framework (sla_id, framework_id)
                )
            """)
            
            self.stdout.write(
                self.style.SUCCESS('Successfully created compliance_mapping table')
            )
