# Backup and Disaster Recovery Implementation Guide
## For GRC (Governance, Risk, Compliance) and TPRM (Third-Party Risk Management) Systems

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [What is Backup and Disaster Recovery?](#what-is-backup-and-disaster-recovery)
3. [Current System Architecture](#current-system-architecture)
4. [Current Backup Status](#current-backup-status)
5. [Comprehensive Backup Strategy](#comprehensive-backup-strategy)
6. [Disaster Recovery Plan](#disaster-recovery-plan)
7. [Multi-Tenant Considerations](#multi-tenant-considerations)
8. [Implementation Roadmap](#implementation-roadmap)
9. [Technical Implementation Details](#technical-implementation-details)
10. [Monitoring and Reporting](#monitoring-and-reporting)
11. [Testing and Validation](#testing-and-validation)
12. [Compliance and Governance](#compliance-and-governance)

---

## Executive Summary

This document outlines a comprehensive backup and disaster recovery (BDR) strategy for the GRC and TPRM systems. The implementation will ensure business continuity, data protection, and compliance with regulatory requirements while maintaining tenant isolation in a multi-tenant architecture.

### Key Objectives

- **Recovery Time Objective (RTO)**: 4 hours for critical systems
- **Recovery Point Objective (RPO)**: 1 hour for production data
- **Data Retention**: 7 years for compliance data, 90 days for operational backups
- **Backup Frequency**: Hourly incremental, daily full, weekly archival
- **Geographic Redundancy**: Multi-region backup storage

---

## What is Backup and Disaster Recovery?

### Backup

**Backup** is the process of creating copies of data, applications, and system configurations that can be used to restore systems in case of data loss, corruption, or system failure.

**Key Concepts:**
- **Full Backup**: Complete copy of all data at a point in time
- **Incremental Backup**: Only changes since the last backup
- **Differential Backup**: Changes since the last full backup
- **Snapshot**: Point-in-time copy of a system state

### Disaster Recovery

**Disaster Recovery (DR)** is the process of restoring IT infrastructure and operations after a catastrophic event (natural disasters, cyberattacks, hardware failures, human error).

**Key Metrics:**
- **RTO (Recovery Time Objective)**: Maximum acceptable downtime
- **RPO (Recovery Point Objective)**: Maximum acceptable data loss
- **MTTR (Mean Time To Recovery)**: Average time to restore service

### Why It Matters for GRC/TPRM

1. **Regulatory Compliance**: SOX, GDPR, HIPAA require data protection
2. **Business Continuity**: Critical business processes depend on these systems
3. **Data Integrity**: Audit trails and compliance records must be preserved
4. **Multi-Tenant Isolation**: Each tenant's data must be protected separately
5. **Vendor Risk Management**: Third-party data requires special protection

---

## Current System Architecture

### Database Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GRC System                            │
├─────────────────────────────────────────────────────────┤
│  Database: MySQL (grc2)                                 │
│  Location: AWS RDS (ap-south-1)                         │
│  Multi-Tenant: Yes (TenantId in all tables)             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    TPRM System                          │
├─────────────────────────────────────────────────────────┤
│  Database: MySQL (tprm_integration)                     │
│  Location: AWS RDS (ap-south-1)                         │
│  Multi-Tenant: Yes (TenantId in all tables)             │
└─────────────────────────────────────────────────────────┘
```

### File Storage Architecture

```
┌─────────────────────────────────────────────────────────┐
│              File Storage Components                     │
├─────────────────────────────────────────────────────────┤
│  • MEDIA_ROOT: User-uploaded files                      │
│  • TEMP_MEDIA_ROOT: Temporary processing files          │
│  • S3 Integration: External file storage microservice   │
│  • Static Files: Frontend assets                        │
└─────────────────────────────────────────────────────────┘
```

### Application Stack

- **Backend**: Django (Python)
- **Frontend**: Vue.js
- **Task Queue**: Celery
- **Database**: MySQL (RDS)
- **File Storage**: Local filesystem + S3 microservice

---

## Current Backup Status

### What Exists

1. **Basic Contract Module Backups**
   - Location: `backups/contracts/`
   - Format: JSON exports
   - Trigger: Manual before critical operations
   - Scope: Limited to contracts, vendors, terms, clauses

2. **Vendor Backup Manager**
   - Location: `tprm_backend/database/vendor_sqlalchemy_manager.py`
   - Format: SQL dumps (via django-dbbackup)
   - Scheduling: Celery tasks (`vendor_create_scheduled_backup`)
   - Storage: Local filesystem

3. **Django-dbbackup Library**
   - Status: Present in requirements but commented out in settings
   - Capability: Database backup/restore commands

### What's Missing

1. ❌ Comprehensive backup strategy for all databases
2. ❌ Automated file backup (MEDIA_ROOT, S3)
3. ❌ Configuration backup (settings, environment variables)
4. ❌ Multi-tier storage (hot, warm, cold)
5. ❌ Off-site/geographic redundancy
6. ❌ Backup encryption
7. ❌ Backup verification and testing
8. ❌ Tenant-specific backup isolation
9. ❌ Disaster recovery procedures
10. ❌ RTO/RPO measurement and monitoring
11. ❌ Backup monitoring dashboards
12. ❌ Automated restore testing

---

## Comprehensive Backup Strategy

### 1. Database Backup Strategy

#### Backup Types

**Full Backups**
- **Frequency**: Daily at 2:00 AM UTC
- **Retention**: 30 days in hot storage, 90 days in warm storage
- **Format**: Compressed SQL dumps (`.sql.gz`)
- **Scope**: Complete database including all tenants

**Incremental Backups**
- **Frequency**: Every 6 hours
- **Retention**: 7 days
- **Format**: Binary log files (MySQL binlog)
- **Scope**: Transaction logs since last full backup

**Point-in-Time Recovery**
- **Capability**: Restore to any point in last 7 days
- **Method**: Full backup + binary logs
- **Use Case**: Data corruption, accidental deletion

#### Implementation Approach

```python
# Example: Database Backup Service
class DatabaseBackupService:
    """
    Comprehensive database backup service supporting:
    - Full backups (mysqldump)
    - Incremental backups (binary logs)
    - Point-in-time recovery
    - Compression and encryption
    """
    
    def create_full_backup(self, database_name, tenant_id=None):
        """
        Create full database backup
        
        Args:
            database_name: 'grc2' or 'tprm_integration'
            tenant_id: Optional tenant filter for tenant-specific backup
        """
        pass
    
    def create_incremental_backup(self, database_name):
        """Create incremental backup using binary logs"""
        pass
    
    def verify_backup(self, backup_file):
        """Verify backup integrity"""
        pass
```

#### Backup Tools

**For MySQL:**
- `mysqldump`: Full database dumps
- `mysqlbinlog`: Binary log extraction for incremental backups
- `Percona XtraBackup`: Hot backups without locking (for large databases)

**For Django:**
- `django-dbbackup`: Django management commands
- Custom Celery tasks: Scheduled backups

### 2. File Backup Strategy

#### Backup Components

**MEDIA_ROOT**
- **Content**: User-uploaded documents, attachments, reports
- **Frequency**: Daily incremental, weekly full
- **Method**: File system sync (rsync) or S3 sync
- **Size**: Variable (depends on usage)

**TEMP_MEDIA_ROOT**
- **Content**: Temporary processing files
- **Frequency**: Weekly (optional, can be excluded)
- **Method**: Archive and compress

**S3 Files**
- **Content**: Files stored in S3 microservice
- **Frequency**: Daily (via S3 versioning or replication)
- **Method**: S3 cross-region replication or backup bucket

**Static Files**
- **Content**: Frontend assets, compiled JavaScript/CSS
- **Frequency**: On deployment (versioned in Git)
- **Method**: Git repository (primary), backup on deployment

#### Implementation Approach

```python
# Example: File Backup Service
class FileBackupService:
    """
    File system backup service supporting:
    - MEDIA_ROOT backup
    - S3 file backup
    - Compression and deduplication
    """
    
    def backup_media_root(self, tenant_id=None):
        """Backup MEDIA_ROOT with optional tenant filtering"""
        pass
    
    def backup_s3_files(self):
        """Backup files from S3 microservice"""
        pass
    
    def sync_to_backup_storage(self, source, destination):
        """Sync files to backup storage"""
        pass
```

### 3. Configuration Backup Strategy

#### Backup Components

**Django Settings**
- Files: `settings.py`, environment variables
- Frequency: On change (version control)
- Method: Git repository + encrypted backup

**Database Configuration**
- Connection strings, credentials
- Frequency: On change
- Method: Encrypted secrets manager (AWS Secrets Manager, HashiCorp Vault)

**Infrastructure Configuration**
- Docker Compose files
- Deployment scripts
- Frequency: On change
- Method: Git repository

**SSL Certificates**
- TLS certificates and keys
- Frequency: On renewal
- Method: Encrypted backup storage

### 4. Backup Storage Tiers

#### Hot Storage (Fast Access)
- **Purpose**: Recent backups for quick restore
- **Retention**: 7 days
- **Location**: Local SSD or fast S3
- **Use Case**: Recent data loss, quick recovery

#### Warm Storage (Standard Access)
- **Purpose**: Regular backups
- **Retention**: 30-90 days
- **Location**: S3 Standard
- **Use Case**: Weekly/monthly recovery needs

#### Cold Storage (Archive)
- **Purpose**: Long-term retention for compliance
- **Retention**: 7 years
- **Location**: S3 Glacier or S3 Glacier Deep Archive
- **Use Case**: Compliance audits, historical data

#### Implementation

```
backup_storage/
├── hot/
│   ├── grc2/
│   │   ├── full_20240101_020000.sql.gz
│   │   └── incremental_20240101_080000.binlog
│   └── tprm_integration/
│       └── ...
├── warm/
│   └── ...
└── cold/
    └── ...
```

### 5. Backup Encryption

#### Requirements

- **At Rest**: All backups encrypted using AES-256
- **In Transit**: TLS 1.3 for backup transfers
- **Key Management**: AWS KMS or similar
- **Key Rotation**: Quarterly

#### Implementation

```python
# Example: Encrypted Backup
from cryptography.fernet import Fernet
import boto3

class EncryptedBackupService:
    def encrypt_backup(self, backup_file, key_id):
        """Encrypt backup using KMS key"""
        kms = boto3.client('kms')
        # Generate data key
        # Encrypt backup
        # Store encrypted backup
        pass
```

### 6. Backup Compression

#### Strategy

- **Database Backups**: gzip compression (60-80% size reduction)
- **File Backups**: tar.gz for multiple files
- **Binary Logs**: Compress before archival

#### Benefits

- Reduced storage costs
- Faster transfer times
- Lower bandwidth usage

---

## Disaster Recovery Plan

### Recovery Objectives

#### RTO (Recovery Time Objective)

| System Component | RTO Target | Priority |
|-----------------|------------|----------|
| GRC Database | 2 hours | Critical |
| TPRM Database | 2 hours | Critical |
| Application Servers | 4 hours | High |
| File Storage | 6 hours | Medium |
| Full System | 8 hours | High |

#### RPO (Recovery Point Objective)

| Data Type | RPO Target | Backup Frequency |
|-----------|------------|------------------|
| Database Transactions | 1 hour | 6-hour incremental |
| User Files | 24 hours | Daily |
| Configuration | 0 (versioned) | On change |

### Disaster Scenarios

#### Scenario 1: Database Corruption

**Symptoms:**
- Database errors, corrupted tables
- Data integrity issues

**Recovery Steps:**
1. Identify corruption extent
2. Stop application services
3. Restore from last known good backup
4. Apply binary logs up to corruption point (if possible)
5. Verify data integrity
6. Resume services

**RTO**: 2-4 hours
**RPO**: Up to 6 hours (last incremental backup)

#### Scenario 2: Region Outage

**Symptoms:**
- Complete AWS region unavailable
- Database and application servers down

**Recovery Steps:**
1. Activate disaster recovery region
2. Restore database from cross-region backup
3. Deploy application servers in DR region
4. Update DNS/routing
5. Verify functionality
6. Resume operations

**RTO**: 4-8 hours
**RPO**: Up to 24 hours (last daily backup)

#### Scenario 3: Ransomware/Cyberattack

**Symptoms:**
- Encrypted files
- Unauthorized access
- Data exfiltration

**Recovery Steps:**
1. Isolate affected systems
2. Assess damage extent
3. Restore from clean backup (before infection)
4. Patch security vulnerabilities
5. Reset credentials
6. Verify no backdoors remain
7. Resume operations with enhanced monitoring

**RTO**: 8-24 hours
**RPO**: Up to 24 hours (last clean backup)

#### Scenario 4: Accidental Data Deletion

**Symptoms:**
- Missing records or files
- User reports data loss

**Recovery Steps:**
1. Identify deletion scope and time
2. Restore from point-in-time backup
3. Verify restored data
4. Resume operations

**RTO**: 1-2 hours
**RPO**: Up to 1 hour (point-in-time recovery)

### Failover Mechanisms

#### Automated Failover

**Database Replication**
- Master-slave replication for MySQL
- Automatic promotion of slave on master failure
- Health checks every 30 seconds

**Application Load Balancing**
- Multiple application servers
- Health checks and automatic failover
- Session persistence

#### Manual Failover

**Runbook-Based**
- Step-by-step procedures
- Approval gates for critical steps
- Audit logging

### Multi-Region Setup

```
Primary Region (ap-south-1)
├── GRC Database (Master)
├── TPRM Database (Master)
├── Application Servers
└── File Storage

Secondary Region (us-east-1) - DR
├── GRC Database (Replica)
├── TPRM Database (Replica)
├── Standby Application Servers
└── Backup Storage
```

---

## Multi-Tenant Considerations

### Tenant-Specific Backups

#### Requirements

1. **Isolation**: Each tenant's backup must be isolated
2. **Access Control**: Tenants can only access their own backups
3. **Self-Service**: Tenant admins can create on-demand backups
4. **Restore Control**: Tenant admins can restore their own data (with approval)

#### Implementation

```python
# Example: Tenant-Aware Backup
class TenantBackupService:
    def create_tenant_backup(self, tenant_id):
        """Create backup for specific tenant"""
        # Filter database by tenant_id
        # Backup only tenant's data
        # Store in tenant-specific path
        pass
    
    def restore_tenant_backup(self, tenant_id, backup_id):
        """Restore tenant data from backup"""
        # Validate tenant access
        # Restore only tenant's data
        # Maintain tenant isolation
        pass
```

#### Backup Storage Structure

```
backups/
├── tenants/
│   ├── tenant_1/
│   │   ├── database/
│   │   │   ├── full_20240101.sql.gz
│   │   │   └── incremental_20240101_080000.binlog
│   │   └── files/
│   │       └── media_root_20240101.tar.gz
│   └── tenant_2/
│       └── ...
└── system/
    └── (system-wide backups)
```

### Tenant Backup API

#### Endpoints

```
POST /api/backups/tenant/create
GET /api/backups/tenant/list
GET /api/backups/tenant/{backup_id}
POST /api/backups/tenant/{backup_id}/restore
DELETE /api/backups/tenant/{backup_id}
```

#### Access Control

- Tenants can only see their own backups
- Restore requires approval workflow
- Audit logging for all backup operations

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)

**Week 1-2: Database Backup Infrastructure**
- [ ] Set up database backup service
- [ ] Implement full backup (mysqldump)
- [ ] Implement incremental backup (binary logs)
- [ ] Add compression and encryption
- [ ] Create backup storage structure

**Week 3-4: File Backup Infrastructure**
- [ ] Implement MEDIA_ROOT backup
- [ ] Implement S3 file backup
- [ ] Add file compression and deduplication
- [ ] Set up file backup scheduling

### Phase 2: Automation (Weeks 5-8)

**Week 5-6: Automated Scheduling**
- [ ] Set up Celery beat schedules
- [ ] Implement backup job orchestration
- [ ] Add retry logic and error handling
- [ ] Create backup status tracking

**Week 7-8: Multi-Tier Storage**
- [ ] Implement hot/warm/cold storage tiers
- [ ] Set up S3 lifecycle policies
- [ ] Implement automatic tier migration
- [ ] Add storage cost monitoring

### Phase 3: Multi-Tenant Support (Weeks 9-12)

**Week 9-10: Tenant Isolation**
- [ ] Implement tenant-specific backup creation
- [ ] Add tenant backup storage isolation
- [ ] Create tenant backup API endpoints
- [ ] Implement access controls

**Week 11-12: Self-Service Features**
- [ ] Build tenant backup dashboard
- [ ] Implement on-demand backup creation
- [ ] Add restore request workflow
- [ ] Create tenant backup history views

### Phase 4: Disaster Recovery (Weeks 13-16)

**Week 13-14: DR Infrastructure**
- [ ] Set up secondary region
- [ ] Implement database replication
- [ ] Configure cross-region backup sync
- [ ] Create DR runbooks

**Week 15-16: Failover Mechanisms**
- [ ] Implement automated failover
- [ ] Create manual failover procedures
- [ ] Set up health checks
- [ ] Test failover scenarios

### Phase 5: Monitoring and Testing (Weeks 17-20)

**Week 17-18: Monitoring**
- [ ] Build backup monitoring dashboard
- [ ] Implement alerting for failures
- [ ] Add backup success rate tracking
- [ ] Create storage usage reports

**Week 19-20: Testing and Validation**
- [ ] Implement automated restore testing
- [ ] Conduct disaster recovery drills
- [ ] Measure RTO/RPO metrics
- [ ] Create compliance reports

---

## Technical Implementation Details

### 1. Database Backup Service

#### File Structure

```
grc_backend/
├── grc/
│   ├── services/
│   │   ├── backup/
│   │   │   ├── __init__.py
│   │   │   ├── database_backup.py
│   │   │   ├── file_backup.py
│   │   │   ├── config_backup.py
│   │   │   ├── encryption.py
│   │   │   └── storage_manager.py
│   │   └── ...
│   └── tasks/
│       └── backup_tasks.py
```

#### Database Backup Implementation

```python
# grc/services/backup/database_backup.py
import subprocess
import gzip
import os
from datetime import datetime
from pathlib import Path
from django.conf import settings
from .encryption import encrypt_backup
from .storage_manager import StorageManager

class DatabaseBackupService:
    """Comprehensive database backup service"""
    
    def __init__(self):
        self.storage_manager = StorageManager()
        self.backup_dir = Path(settings.BASE_DIR) / 'backups' / 'database'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_full_backup(self, database_name, tenant_id=None):
        """
        Create full database backup
        
        Args:
            database_name: 'grc2' or 'tprm_integration'
            tenant_id: Optional tenant filter
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f"{database_name}_full_{timestamp}.sql"
        
        # Get database credentials from settings
        db_config = settings.DATABASES.get(database_name) or settings.DATABASES['default']
        
        # Create mysqldump command
        cmd = [
            'mysqldump',
            f"--host={db_config['HOST']}",
            f"--port={db_config['PORT']}",
            f"--user={db_config['USER']}",
            f"--password={db_config['PASSWORD']}",
            '--single-transaction',
            '--routines',
            '--triggers',
            '--events',
            database_name
        ]
        
        # Add tenant filter if specified
        if tenant_id:
            cmd.extend(['--where', f'TenantId={tenant_id}'])
        
        # Execute backup
        with open(backup_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            raise Exception(f"Backup failed: {result.stderr.decode()}")
        
        # Compress backup
        compressed_file = self.compress_backup(backup_file)
        
        # Encrypt backup
        encrypted_file = encrypt_backup(compressed_file)
        
        # Upload to storage
        storage_path = self.storage_manager.upload_to_hot_storage(
            encrypted_file, 
            database_name,
            tenant_id
        )
        
        # Clean up local file
        backup_file.unlink()
        compressed_file.unlink()
        encrypted_file.unlink()
        
        return {
            'backup_id': timestamp,
            'database': database_name,
            'tenant_id': tenant_id,
            'storage_path': storage_path,
            'size': encrypted_file.stat().st_size,
            'created_at': datetime.now().isoformat()
        }
    
    def compress_backup(self, backup_file):
        """Compress backup file using gzip"""
        compressed_file = Path(f"{backup_file}.gz")
        with open(backup_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                f_out.writelines(f_in)
        return compressed_file
    
    def create_incremental_backup(self, database_name):
        """Create incremental backup using binary logs"""
        # Implementation for binary log backup
        pass
    
    def verify_backup(self, backup_file):
        """Verify backup integrity"""
        # Check file exists
        # Verify checksum
        # Test restore to temporary database
        pass
```

### 2. File Backup Service

```python
# grc/services/backup/file_backup.py
import tarfile
import gzip
from pathlib import Path
from django.conf import settings
from .encryption import encrypt_backup
from .storage_manager import StorageManager

class FileBackupService:
    """File system backup service"""
    
    def __init__(self):
        self.storage_manager = StorageManager()
        self.backup_dir = Path(settings.BASE_DIR) / 'backups' / 'files'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def backup_media_root(self, tenant_id=None):
        """Backup MEDIA_ROOT directory"""
        media_root = Path(settings.MEDIA_ROOT)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f"media_root_{timestamp}.tar.gz"
        
        # Create tar archive
        with tarfile.open(backup_file, 'w:gz') as tar:
            if tenant_id:
                # Backup only tenant-specific files
                tenant_path = media_root / f"tenant_{tenant_id}"
                if tenant_path.exists():
                    tar.add(tenant_path, arcname=f"tenant_{tenant_id}")
            else:
                # Backup entire MEDIA_ROOT
                tar.add(media_root, arcname='media_root')
        
        # Encrypt and upload
        encrypted_file = encrypt_backup(backup_file)
        storage_path = self.storage_manager.upload_to_hot_storage(
            encrypted_file,
            'media_root',
            tenant_id
        )
        
        # Clean up
        backup_file.unlink()
        encrypted_file.unlink()
        
        return {
            'backup_id': timestamp,
            'type': 'media_root',
            'tenant_id': tenant_id,
            'storage_path': storage_path,
            'size': encrypted_file.stat().st_size
        }
```

### 3. Celery Backup Tasks

```python
# grc/tasks/backup_tasks.py
from celery import shared_task
from django.conf import settings
from grc.services.backup.database_backup import DatabaseBackupService
from grc.services.backup.file_backup import FileBackupService
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def create_database_backup(self, database_name, tenant_id=None):
    """Celery task for database backup"""
    try:
        service = DatabaseBackupService()
        result = service.create_full_backup(database_name, tenant_id)
        logger.info(f"Backup created: {result['backup_id']}")
        return result
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes

@shared_task
def create_incremental_backup(database_name):
    """Create incremental database backup"""
    service = DatabaseBackupService()
    return service.create_incremental_backup(database_name)

@shared_task
def backup_media_root(tenant_id=None):
    """Backup MEDIA_ROOT files"""
    service = FileBackupService()
    return service.backup_media_root(tenant_id)

@shared_task
def cleanup_old_backups():
    """Clean up old backups based on retention policy"""
    # Implementation for cleanup
    pass
```

### 4. Celery Beat Schedule

```python
# grc_backend/backend/settings.py

CELERY_BEAT_SCHEDULE = {
    # Daily full database backups
    'backup-grc-daily': {
        'task': 'grc.tasks.backup_tasks.create_database_backup',
        'schedule': crontab(hour=2, minute=0),  # 2 AM UTC
        'args': ('grc2', None),
    },
    'backup-tprm-daily': {
        'task': 'grc.tasks.backup_tasks.create_database_backup',
        'schedule': crontab(hour=2, minute=30),  # 2:30 AM UTC
        'args': ('tprm_integration', None),
    },
    
    # Incremental backups every 6 hours
    'backup-grc-incremental': {
        'task': 'grc.tasks.backup_tasks.create_incremental_backup',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
        'args': ('grc2',),
    },
    
    # Daily file backups
    'backup-media-root': {
        'task': 'grc.tasks.backup_tasks.backup_media_root',
        'schedule': crontab(hour=3, minute=0),  # 3 AM UTC
    },
    
    # Weekly cleanup
    'cleanup-old-backups': {
        'task': 'grc.tasks.backup_tasks.cleanup_old_backups',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),  # Sunday 4 AM
    },
}
```

### 5. Backup Models

```python
# grc/models.py (add to existing models)

class Backup(models.Model):
    """Backup record model"""
    backup_id = models.AutoField(primary_key=True)
    backup_type = models.CharField(max_length=50, choices=[
        ('database_full', 'Database Full'),
        ('database_incremental', 'Database Incremental'),
        ('file_media', 'Media Files'),
        ('file_s3', 'S3 Files'),
        ('config', 'Configuration'),
    ])
    database_name = models.CharField(max_length=100, null=True, blank=True)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, null=True, blank=True)
    storage_path = models.CharField(max_length=500)
    storage_tier = models.CharField(max_length=20, choices=[
        ('hot', 'Hot'),
        ('warm', 'Warm'),
        ('cold', 'Cold'),
    ])
    size_bytes = models.BigIntegerField()
    status = models.CharField(max_length=20, choices=[
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('verified', 'Verified'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'backups'
        indexes = [
            models.Index(fields=['tenant', 'backup_type', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
```

### 6. Backup API Endpoints

```python
# grc/routes/Backup/backup_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from grc.services.backup.database_backup import DatabaseBackupService
from grc.services.backup.file_backup import FileBackupService
from grc.tasks.backup_tasks import create_database_backup, backup_media_root
from grc.decorators import tenant_filter

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@tenant_filter
def create_tenant_backup(request):
    """Create on-demand backup for tenant"""
    tenant_id = request.tenant_id
    
    # Create database backup
    db_task = create_database_backup.delay('grc2', tenant_id)
    
    # Create file backup
    file_task = backup_media_root.delay(tenant_id)
    
    return Response({
        'database_backup_task_id': db_task.id,
        'file_backup_task_id': file_task.id,
        'status': 'initiated'
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@tenant_filter
def list_tenant_backups(request):
    """List backups for tenant"""
    tenant_id = request.tenant_id
    backups = Backup.objects.filter(tenant_id=tenant_id).order_by('-created_at')
    
    return Response({
        'backups': [{
            'backup_id': b.backup_id,
            'type': b.backup_type,
            'size': b.size_bytes,
            'status': b.status,
            'created_at': b.created_at.isoformat(),
        } for b in backups]
    })
```

---

## Monitoring and Reporting

### Backup Monitoring Dashboard

#### Key Metrics

1. **Backup Success Rate**
   - Percentage of successful backups
   - Target: >99%

2. **Backup Duration**
   - Time to complete backups
   - Alert if exceeds threshold

3. **Storage Usage**
   - Total backup storage used
   - Projected growth
   - Cost tracking

4. **Last Backup Time**
   - Per database, per tenant
   - Alert if backup is overdue

5. **Backup Verification Status**
   - Number of verified backups
   - Failed verifications

#### Implementation

```python
# grc/services/backup/monitoring.py
from django.utils import timezone
from datetime import timedelta
from grc.models import Backup

class BackupMonitoringService:
    def get_backup_health(self):
        """Get overall backup health status"""
        last_24h = timezone.now() - timedelta(hours=24)
        
        recent_backups = Backup.objects.filter(
            created_at__gte=last_24h,
            status='completed'
        )
        
        total_backups = recent_backups.count()
        successful_backups = recent_backups.filter(status='completed').count()
        
        success_rate = (successful_backups / total_backups * 100) if total_backups > 0 else 0
        
        return {
            'success_rate': success_rate,
            'total_backups_24h': total_backups,
            'successful_backups': successful_backups,
            'failed_backups': total_backups - successful_backups,
            'health_status': 'healthy' if success_rate >= 99 else 'degraded'
        }
```

### Alerting

#### Alert Conditions

1. **Backup Failure**: Immediate alert
2. **Backup Overdue**: Alert if backup is >2 hours late
3. **Storage Capacity**: Alert if storage >80% full
4. **Verification Failure**: Alert if backup verification fails
5. **RTO/RPO Violation**: Alert if recovery times exceed targets

#### Alert Channels

- Email: For critical alerts
- SMS: For urgent issues
- Slack/Teams: For team notifications
- PagerDuty: For on-call escalation

---

## Testing and Validation

### Automated Restore Testing

#### Weekly Restore Tests

```python
# grc/tasks/backup_tasks.py

@shared_task
def test_backup_restore(backup_id):
    """Test restore from backup"""
    # 1. Create temporary database
    # 2. Restore backup to temporary database
    # 3. Verify data integrity
    # 4. Clean up temporary database
    # 5. Record test results
    pass
```

### Disaster Recovery Drills

#### Quarterly DR Drills

1. **Scenario Selection**: Random disaster scenario
2. **Execution**: Follow runbook procedures
3. **Measurement**: Record RTO and RPO
4. **Documentation**: Document issues and improvements
5. **Improvement**: Update procedures based on findings

### Backup Verification

#### Integrity Checks

- File checksums (MD5, SHA256)
- Database consistency checks
- Restore to test environment
- Data sampling and validation

---

## Compliance and Governance

### Regulatory Requirements

#### SOX (Sarbanes-Oxley)
- 7-year retention for financial records
- Audit trail of backup operations
- Access controls and segregation of duties

#### GDPR (General Data Protection Regulation)
- Right to erasure (backup deletion)
- Data portability (backup export)
- Encryption requirements

#### HIPAA (Health Insurance Portability)
- Encryption of PHI in backups
- Access logging
- Business associate agreements

### Backup Governance

#### Access Controls

- Role-based access to backups
- Approval workflows for restore
- Audit logging of all operations

#### Retention Policies

```python
RETENTION_POLICIES = {
    'compliance_data': {
        'retention_days': 2555,  # 7 years
        'storage_tier': 'cold',
    },
    'operational_data': {
        'retention_days': 90,
        'storage_tier': 'warm',
    },
    'temporary_data': {
        'retention_days': 7,
        'storage_tier': 'hot',
    },
}
```

#### Audit Logging

All backup operations must be logged:
- Who created/restored backup
- When operation occurred
- What data was backed up/restored
- Where backup is stored
- Verification status

---

## Best Practices

### 1. Backup Strategy

- ✅ Follow 3-2-1 rule: 3 copies, 2 different media, 1 off-site
- ✅ Test backups regularly (restore tests)
- ✅ Encrypt all backups
- ✅ Document backup procedures
- ✅ Monitor backup success rates

### 2. Disaster Recovery

- ✅ Define clear RTO/RPO targets
- ✅ Document runbooks for common scenarios
- ✅ Conduct regular DR drills
- ✅ Maintain secondary region
- ✅ Automate failover where possible

### 3. Multi-Tenant Considerations

- ✅ Isolate tenant backups
- ✅ Enforce access controls
- ✅ Provide self-service options
- ✅ Audit tenant backup operations
- ✅ Support tenant data export

### 4. Security

- ✅ Encrypt backups at rest and in transit
- ✅ Use key management services
- ✅ Rotate encryption keys regularly
- ✅ Limit backup access to authorized personnel
- ✅ Monitor for unauthorized access

---

## Conclusion

This comprehensive backup and disaster recovery strategy provides:

1. **Data Protection**: Multiple backup types and storage tiers
2. **Business Continuity**: Clear RTO/RPO targets and recovery procedures
3. **Compliance**: Meets regulatory requirements for data retention
4. **Multi-Tenant Support**: Tenant isolation and self-service capabilities
5. **Monitoring**: Real-time visibility into backup health
6. **Testing**: Regular validation of backup and recovery processes

### Next Steps

1. Review and approve this strategy
2. Allocate resources for implementation
3. Begin Phase 1 implementation
4. Establish backup monitoring
5. Conduct first DR drill after implementation

---

## Appendix

### A. Backup Tools Comparison

| Tool | Type | Pros | Cons |
|------|------|------|------|
| mysqldump | Database | Simple, built-in | Locks tables |
| Percona XtraBackup | Database | Hot backup, no locks | More complex |
| django-dbbackup | Django | Django integration | Limited features |
| rsync | Files | Fast, efficient | No versioning |
| S3 Versioning | Cloud | Automatic, scalable | Cost at scale |

### B. Storage Cost Estimation

**Assumptions:**
- Database size: 100 GB
- File storage: 500 GB
- Backup compression: 70% reduction
- Retention: 90 days hot, 7 years cold

**Estimated Monthly Costs (AWS):**
- S3 Standard (hot): $23/month
- S3 Standard (warm): $23/month
- S3 Glacier (cold): $1/month
- **Total**: ~$47/month

### C. RTO/RPO Measurement

```python
# Example: RTO/RPO Measurement
class RecoveryMetrics:
    def measure_rto(self, disaster_start, service_restored):
        """Measure Recovery Time Objective"""
        rto = (service_restored - disaster_start).total_seconds() / 3600
        return rto
    
    def measure_rpo(self, last_backup, disaster_start):
        """Measure Recovery Point Objective"""
        rpo = (disaster_start - last_backup).total_seconds() / 3600
        return rpo
```

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-01  
**Author**: GRC/TPRM Development Team  
**Status**: Draft for Review

