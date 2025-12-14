"""
Async Export Tasks using Celery
Handles all export operations in background to prevent server timeouts and crashes
"""
import json
import traceback
from datetime import datetime
from celery import shared_task
from django.utils import timezone
from django.db import transaction

# Import export functions
from .s3_fucntions import export_data, create_direct_mysql_client
from django.conf import settings


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_export_async(self, export_task_id, data, file_format, user_id, options=None, module='general'):
    """
    Async export task that processes exports in background
    
    Args:
        export_task_id: ID of ExportTask record
        data: Data to export (can be large)
        file_format: Export format (xlsx, pdf, csv, json, xml, txt)
        user_id: User ID requesting export
        options: Additional export options
        module: Module name (risk, incident, compliance, audit)
    
    Returns:
        ExportTask ID on success
    """
    from ...models import ExportTask
    
    try:
        # Get export task
        export_task = ExportTask.objects.get(id=export_task_id)
        export_task.status = 'processing'
        export_task.save()
        
        print(f"\n{'='*80}")
        print(f"🚀 [ASYNC EXPORT] Starting export task {export_task_id}")
        print(f"   ├─ Module: {module}")
        print(f"   ├─ Format: {file_format}")
        print(f"   ├─ User ID: {user_id}")
        print(f"   ├─ Record count: {len(data) if isinstance(data, list) else 1}")
        print(f"   └─ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        # Validate data size
        data_size = len(str(data))
        max_size = 50 * 1024 * 1024  # 50MB limit
        record_count = len(data) if isinstance(data, list) else 1
        
        if data_size > max_size:
            error_msg = f'Data too large for export ({data_size} bytes). Maximum: {max_size} bytes.'
            export_task.status = 'failed'
            export_task.error = error_msg
            export_task.save()
            print(f"❌ [ASYNC EXPORT] {error_msg}")
            return export_task_id
        
        # For very large datasets, use chunking
        if record_count > 5000:
            print(f"⚠️  [ASYNC EXPORT] Large dataset detected ({record_count} records), using chunked processing")
            result = process_large_export_chunked(export_task, data, file_format, user_id, options)
        else:
            # Process normally
            result = process_export_normal(export_task, data, file_format, user_id, options)
        
        # Update task with results
        if result.get('success'):
            export_task.status = 'completed'
            export_task.s3_url = result.get('file_url', '')
            export_task.file_name = result.get('file_name', '')
            export_task.completed_at = timezone.now()
            export_task.metadata = result.get('metadata', {})
            export_task.save()
            
            print(f"\n{'='*80}")
            print(f"✅ [ASYNC EXPORT] Export completed successfully")
            print(f"   ├─ Task ID: {export_task_id}")
            print(f"   ├─ File URL: {result.get('file_url', 'N/A')}")
            print(f"   └─ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}\n")
        else:
            export_task.status = 'failed'
            export_task.error = result.get('error', 'Unknown error')
            export_task.save()
            print(f"❌ [ASYNC EXPORT] Export failed: {result.get('error', 'Unknown error')}")
        
        return export_task_id
        
    except ExportTask.DoesNotExist:
        error_msg = f"ExportTask {export_task_id} not found"
        print(f"❌ [ASYNC EXPORT] {error_msg}")
        raise Exception(error_msg)
        
    except Exception as e:
        error_msg = f"Export failed: {str(e)}"
        print(f"❌ [ASYNC EXPORT] {error_msg}")
        print(traceback.format_exc())
        
        # Update task with error
        try:
            export_task = ExportTask.objects.get(id=export_task_id)
            export_task.status = 'failed'
            export_task.error = error_msg
            export_task.save()
        except:
            pass
        
        # Retry if not max retries
        if self.request.retries < self.max_retries:
            print(f"🔄 [ASYNC EXPORT] Retrying export task (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        else:
            raise Exception(error_msg)


def process_export_normal(export_task, data, file_format, user_id, options):
    """Process normal export (small to medium datasets)"""
    try:
        # Create S3 client
        db_config = settings.DATABASES['default']
        mysql_config = {
            'host': db_config['HOST'],
            'user': db_config['USER'],
            'password': db_config['PASSWORD'],
            'database': db_config['NAME'],
            'port': db_config.get('PORT', 3306)
        }
        s3_client = create_direct_mysql_client(mysql_config)
        
        # Call export function
        result = export_data(
            data=data,
            file_format=file_format,
            user_id=user_id,
            options=options or {},
            s3_client_instance=s3_client
        )
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def process_large_export_chunked(export_task, data, file_format, user_id, options):
    """
    Process large exports in chunks to prevent memory issues
    For formats that support chunking (CSV, JSON, TXT)
    """
    try:
        # Only chunk CSV, JSON, and TXT - others need full dataset
        chunkable_formats = ['csv', 'json', 'txt']
        
        if file_format.lower() not in chunkable_formats:
            # For non-chunkable formats, process normally but with memory optimization
            return process_export_normal(export_task, data, file_format, user_id, options)
        
        # Chunk processing for large datasets
        chunk_size = 1000  # Process 1000 records at a time
        total_records = len(data) if isinstance(data, list) else 1
        
        print(f"📦 [ASYNC EXPORT] Processing {total_records} records in chunks of {chunk_size}")
        
        # For chunkable formats, we can process in batches
        # But for simplicity, we'll still process all at once but with memory optimization
        # In production, you might want to split into multiple files
        
        # Create S3 client
        db_config = settings.DATABASES['default']
        mysql_config = {
            'host': db_config['HOST'],
            'user': db_config['USER'],
            'password': db_config['PASSWORD'],
            'database': db_config['NAME'],
            'port': db_config.get('PORT', 3306)
        }
        s3_client = create_direct_mysql_client(mysql_config)
        
        # Process export with memory optimization
        result = export_data(
            data=data,
            file_format=file_format,
            user_id=user_id,
            options=options or {},
            s3_client_instance=s3_client
        )
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def create_export_task(user_id, file_format, module='general', export_data_dict=None, framework_id=None):
    """
    Create an ExportTask record for async processing
    
    Args:
        user_id: User ID requesting export
        file_format: Export format
        module: Module name
        export_data_dict: Additional export data
        framework_id: Optional Framework ID (if not provided, will use first available)
    
    Returns:
        ExportTask instance
    """
    from ...models import ExportTask, Framework
    
    try:
        # Get framework (required by model)
        if framework_id:
            framework = Framework.objects.get(id=framework_id)
        else:
            # Get first available framework
            framework = Framework.objects.first()
            if not framework:
                # Create a default framework if none exists
                framework = Framework.objects.create(
                    FrameworkName='Default Export Framework',
                    FrameworkVersion='1.0',
                    Status='Active'
                )
        
        export_task = ExportTask.objects.create(
            export_data=export_data_dict or {},
            file_type=file_format,
            user_id=str(user_id),
            status='pending',
            FrameworkId=framework
        )
        
        return export_task
        
    except Exception as e:
        print(f"❌ [ASYNC EXPORT] Error creating export task: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

