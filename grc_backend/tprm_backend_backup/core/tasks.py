"""
Celery tasks for the core app.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import AuditLog, FileUpload


@shared_task
def cleanup_old_data():
    """Clean up old data based on retention policies."""
    # Clean up old audit logs (keep for 2 years)
    two_years_ago = timezone.now() - timedelta(days=730)
    AuditLog.objects.filter(created_at__lt=two_years_ago).delete()
    
    # Clean up old file uploads (keep for 1 year)
    one_year_ago = timezone.now() - timedelta(days=365)
    FileUpload.objects.filter(created_at__lt=one_year_ago).delete()
    
    return "Data cleanup completed"


@shared_task
def process_file_upload(file_upload_id):
    """Process uploaded files."""
    try:
        file_upload = FileUpload.objects.get(id=file_upload_id)
        file_upload.processing_status = 'processing'
        file_upload.save()
        
        # Add your file processing logic here
        # For example: parse CSV, validate data, etc.
        
        file_upload.processing_status = 'completed'
        file_upload.is_processed = True
        file_upload.save()
        
        return f"File {file_upload.original_filename} processed successfully"
    except FileUpload.DoesNotExist:
        return f"File upload {file_upload_id} not found"
    except Exception as e:
        file_upload.processing_status = 'failed'
        file_upload.processing_errors.append(str(e))
        file_upload.save()
        return f"Error processing file: {str(e)}"


@shared_task
def generate_system_report():
    """Generate system health report."""
    # Add your system health check logic here
    return "System health report generated"
