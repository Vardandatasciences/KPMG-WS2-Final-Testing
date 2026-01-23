from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Setup external applications database tables and sample data'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Setting up External Applications integration...')
        
        try:
            self.create_tables()
            self.insert_sample_data()
            self.create_indexes()
            
            self.stdout.write(
                self.style.SUCCESS('\n✅ External Applications setup completed successfully!')
            )
            self.stdout.write('\n📋 Next steps:')
            self.stdout.write('1. Restart your Django server')
            self.stdout.write('2. Test the external applications endpoints')
            self.stdout.write('3. Check the frontend integration')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during setup: {e}')
            )

    def create_tables(self):
        """Create external applications tables using raw SQL"""
        
        with connection.cursor() as cursor:
            # Create external_applications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS external_applications (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(255) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    type VARCHAR(100) NOT NULL,
                    description TEXT,
                    icon_class VARCHAR(100),
                    version VARCHAR(50),
                    status ENUM('connected', 'disconnected', 'pending', 'error') DEFAULT 'disconnected',
                    last_sync TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    configuration JSON NULL,
                    api_endpoint VARCHAR(500) NULL,
                    oauth_url VARCHAR(500) NULL,
                    features JSON NULL,
                    UNIQUE KEY unique_name (name)
                )
            """)
            
            # Create external_application_connections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS external_application_connections (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    application_id INT NOT NULL,
                    user_id INT NOT NULL,
                    connection_token TEXT,
                    refresh_token TEXT,
                    token_expires_at TIMESTAMP NULL,
                    connection_status ENUM('active', 'expired', 'revoked', 'error') DEFAULT 'active',
                    last_used TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES external_applications(id) ON DELETE CASCADE,
                    INDEX idx_user_app (user_id, application_id),
                    INDEX idx_status (connection_status)
                )
            """)
            
            # Create external_application_sync_logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS external_application_sync_logs (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    application_id INT NOT NULL,
                    user_id INT NOT NULL,
                    sync_type ENUM('full', 'incremental', 'manual') NOT NULL,
                    sync_status ENUM('success', 'failed', 'partial') NOT NULL,
                    records_synced INT DEFAULT 0,
                    error_message TEXT NULL,
                    sync_started_at TIMESTAMP NOT NULL,
                    sync_completed_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES external_applications(id) ON DELETE CASCADE,
                    INDEX idx_app_sync (application_id, sync_started_at),
                    INDEX idx_user_sync (user_id, sync_started_at)
                )
            """)
            
            self.stdout.write('✅ Database tables created successfully!')

    def insert_sample_data(self):
        """Insert sample data for external applications"""
        
        with connection.cursor() as cursor:
            # Check if data already exists
            cursor.execute("SELECT COUNT(*) FROM external_applications")
            count = cursor.fetchone()[0]
            
            if count > 0:
                self.stdout.write('ℹ️  Sample data already exists, skipping insertion.')
                return
            
            # Insert sample external applications
            sample_apps = [
                (
                    'Microsoft Azure',
                    'Cloud Platform',
                    'Cloud Service',
                    'Connect to Azure Active Directory and Azure services for identity management and cloud resource monitoring.',
                    'fab fa-microsoft',
                    'v2.1.0',
                    'disconnected',
                    None,
                    'https://graph.microsoft.com/v1.0',
                    'https://login.microsoftonline.com/oauth2/v2.0/authorize',
                    '["Active Directory integration", "Cloud resource monitoring", "Identity management", "Compliance reporting"]'
                ),
                (
                    'AWS',
                    'Cloud Platform',
                    'Cloud Service',
                    'Integrate with Amazon Web Services for cloud security monitoring and compliance management.',
                    'fab fa-aws',
                    'v1.8.2',
                    'disconnected',
                    None,
                    'https://aws.amazon.com/api',
                    'https://aws.amazon.com/oauth',
                    '["CloudTrail integration", "Config Rules monitoring", "Security Hub integration", "Cost optimization"]'
                ),
                (
                    'ServiceNow',
                    'ITSM',
                    'Service Management',
                    'Connect to ServiceNow for incident management, change management, and IT service operations.',
                    'fas fa-cogs',
                    'v3.0.1',
                    'disconnected',
                    None,
                    'https://your-instance.service-now.com/api/now',
                    'https://your-instance.service-now.com/oauth_auth.do',
                    '["Incident management", "Change management", "Asset management", "Service catalog"]'
                ),
                (
                    'Splunk',
                    'SIEM',
                    'Security Monitoring',
                    'Integrate with Splunk for security information and event management, log analysis, and threat detection.',
                    'fas fa-shield-alt',
                    'v2.5.0',
                    'disconnected',
                    None,
                    'https://your-splunk-instance:8089/services',
                    'https://your-splunk-instance:8089/services/auth/login',
                    '["Log analysis", "Threat detection", "Security monitoring", "Compliance reporting"]'
                ),
                (
                    'Salesforce',
                    'CRM',
                    'Customer Management',
                    'Connect to Salesforce for customer relationship management and business process automation.',
                    'fab fa-salesforce',
                    'v1.9.3',
                    'disconnected',
                    None,
                    'https://your-instance.salesforce.com/services/data/v58.0',
                    'https://your-instance.salesforce.com/services/oauth2/authorize',
                    '["Customer data management", "Sales pipeline tracking", "Marketing automation", "Analytics and reporting"]'
                ),
                (
                    'Jira',
                    'Project Management',
                    'Issue Tracking',
                    'Integrate with Jira for project management, issue tracking, and agile development workflows.',
                    'fab fa-jira',
                    'v2.2.1',
                    'disconnected',
                    None,
                    'http://localhost:5000/jira-projects',
                    'http://localhost:5000/oauth',
                    '["Issue tracking", "Project management", "Agile workflows", "Time tracking"]'
                )
            ]
            
            for app_data in sample_apps:
                cursor.execute("""
                    INSERT INTO external_applications (
                        name, category, type, description, icon_class, version, 
                        status, last_sync, api_endpoint, oauth_url, features
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, app_data)
            
            self.stdout.write('✅ Sample data inserted successfully!')

    def create_indexes(self):
        """Create additional indexes for performance"""
        
        with connection.cursor() as cursor:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_external_apps_status ON external_applications(status)",
                "CREATE INDEX IF NOT EXISTS idx_external_apps_category ON external_applications(category)",
                "CREATE INDEX IF NOT EXISTS idx_external_apps_updated ON external_applications(updated_at)",
                "CREATE INDEX IF NOT EXISTS idx_connections_token_expires ON external_application_connections(token_expires_at)",
                "CREATE INDEX IF NOT EXISTS idx_sync_logs_status ON external_application_sync_logs(sync_status)",
                "CREATE INDEX IF NOT EXISTS idx_sync_logs_completed ON external_application_sync_logs(sync_completed_at)"
            ]
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    self.stdout.write(f'⚠️  Index creation warning: {e}')
            
            self.stdout.write('✅ Indexes created successfully!')

