"""
Django management command to create TPRM consent tables and insert default configurations
Usage: python manage.py setup_tprm_consent_tables
"""

from django.core.management.base import BaseCommand
from django.db import connections
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create TPRM consent tables and insert default consent configurations'

    def handle(self, *args, **options):
        self.stdout.write('Creating TPRM consent tables...')
        
        # Try to get TPRM connection, fallback to default
        try:
            tprm_connection = connections['tprm'] if 'tprm' in connections.databases else connections['default']
        except:
            tprm_connection = connections['default']
        
        with tprm_connection.cursor() as cursor:
            # Create consent_configuration_tprm table
            self.stdout.write('Creating consent_configuration_tprm table...')
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `consent_configuration_tprm` (
                  `ConfigId` int NOT NULL AUTO_INCREMENT,
                  `ActionType` varchar(50) NOT NULL,
                  `ActionLabel` varchar(100) NOT NULL,
                  `IsEnabled` tinyint(1) NOT NULL DEFAULT '0',
                  `ConsentText` text,
                  `FrameworkId` int DEFAULT '1',
                  `CreatedBy` int DEFAULT NULL,
                  `CreatedAt` datetime DEFAULT CURRENT_TIMESTAMP,
                  `UpdatedBy` int DEFAULT NULL,
                  `UpdatedAt` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                  `retentionExpiry` date DEFAULT NULL,
                  PRIMARY KEY (`ConfigId`),
                  UNIQUE KEY `unique_action_framework` (`ActionType`, `FrameworkId`),
                  KEY `idx_framework` (`FrameworkId`),
                  KEY `idx_action_type` (`ActionType`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # Create consent_acceptance_tprm table
            self.stdout.write('Creating consent_acceptance_tprm table...')
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `consent_acceptance_tprm` (
                  `AcceptanceId` int NOT NULL AUTO_INCREMENT,
                  `UserId` int NOT NULL,
                  `ConfigId` int NOT NULL,
                  `ActionType` varchar(50) NOT NULL,
                  `AcceptedAt` datetime DEFAULT CURRENT_TIMESTAMP,
                  `IpAddress` varchar(50) DEFAULT NULL,
                  `UserAgent` text,
                  `FrameworkId` int DEFAULT '1',
                  `retentionExpiry` date DEFAULT NULL,
                  PRIMARY KEY (`AcceptanceId`),
                  KEY `idx_user_action` (`UserId`, `ActionType`, `AcceptedAt`),
                  KEY `idx_config` (`ConfigId`),
                  KEY `idx_framework` (`FrameworkId`),
                  KEY `idx_user_framework` (`UserId`, `FrameworkId`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # Create consent_withdrawal_tprm table
            self.stdout.write('Creating consent_withdrawal_tprm table...')
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `consent_withdrawal_tprm` (
                  `WithdrawalId` int NOT NULL AUTO_INCREMENT,
                  `UserId` int NOT NULL,
                  `ConfigId` int DEFAULT NULL,
                  `ActionType` varchar(50) NOT NULL,
                  `WithdrawnAt` datetime DEFAULT CURRENT_TIMESTAMP,
                  `IpAddress` varchar(50) DEFAULT NULL,
                  `UserAgent` text,
                  `FrameworkId` int DEFAULT '1',
                  `Reason` text,
                  PRIMARY KEY (`WithdrawalId`),
                  KEY `idx_user_action` (`UserId`, `ActionType`, `WithdrawnAt`),
                  KEY `idx_config` (`ConfigId`),
                  KEY `idx_framework` (`FrameworkId`),
                  KEY `idx_user_framework` (`UserId`, `FrameworkId`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            tprm_connection.commit()
            self.stdout.write(self.style.SUCCESS('✓ TPRM consent tables created successfully'))
            
            # Insert default consent configurations
            self.stdout.write('Inserting default TPRM consent configurations...')
            default_actions = [
                ('tprm_create_sla', 'Create SLA', 'I consent to create SLA. I understand that this action will be recorded and tracked for compliance purposes.'),
                ('tprm_update_sla', 'Update SLA', 'I consent to update SLA. I understand that this action will be recorded and tracked for compliance purposes.'),
                ('tprm_delete_sla', 'Delete SLA', 'I consent to delete SLA. I understand that this action will be recorded and tracked for compliance purposes.'),
                ('tprm_create_vendor', 'Create Vendor', 'I consent to create vendor. I understand that this action will be recorded and tracked for compliance purposes.'),
                ('tprm_update_vendor', 'Update Vendor', 'I consent to update vendor. I understand that this action will be recorded and tracked for compliance purposes.'),
                ('tprm_create_contract', 'Create Contract', 'I consent to create contract. I understand that this action will be recorded and tracked for compliance purposes.'),
                ('tprm_update_contract', 'Update Contract', 'I consent to update contract. I understand that this action will be recorded and tracked for compliance purposes.'),
                ('tprm_create_rfp', 'Create RFP', 'I consent to create RFP. I understand that this action will be recorded and tracked for compliance purposes.'),
                ('tprm_submit_rfp', 'Submit RFP', 'I consent to submit RFP. I understand that this action will be recorded and tracked for compliance purposes.'),
                ('tprm_create_risk', 'Create Risk Assessment', 'I consent to create risk assessment. I understand that this action will be recorded and tracked for compliance purposes.'),
                ('tprm_create_compliance', 'Create Compliance Record', 'I consent to create compliance record. I understand that this action will be recorded and tracked for compliance purposes.'),
            ]
            
            inserted_count = 0
            for action_type, action_label, consent_text in default_actions:
                try:
                    cursor.execute("""
                        INSERT INTO consent_configuration_tprm 
                        (ActionType, ActionLabel, IsEnabled, ConsentText, FrameworkId, CreatedAt, UpdatedAt)
                        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                        ON DUPLICATE KEY UPDATE 
                          ActionLabel = VALUES(ActionLabel),
                          ConsentText = VALUES(ConsentText),
                          UpdatedAt = NOW()
                    """, [action_type, action_label, False, consent_text, 1])
                    inserted_count += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Warning: Could not insert {action_type}: {e}'))
            
            tprm_connection.commit()
            self.stdout.write(self.style.SUCCESS(f'✓ Inserted/Updated {inserted_count} default consent configurations'))
            self.stdout.write(self.style.SUCCESS('\nTPRM consent tables setup completed successfully!'))
            self.stdout.write('\nYou can now:')
            self.stdout.write('  1. Go to Consent Configuration in the admin panel')
            self.stdout.write('  2. Select "TPRM Only" or "All" to see TPRM consents')
            self.stdout.write('  3. Enable "Create SLA" consent to require consent for SLA creation')


