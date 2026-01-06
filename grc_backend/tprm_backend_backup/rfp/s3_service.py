"""
Django Service Wrapper for S3 Microservice Integration
Integrates the S3 microservice client with Django models and provides easy-to-use methods
"""
 
import os
import json
from typing import Dict, List, Optional, Union, Any
from django.conf import settings
from django.utils import timezone
from .models import FileStorage, S3Files
from .s3 import RenderS3Client, create_direct_mysql_client
 
 
class DjangoS3Service:
    """
    Django service wrapper for S3 microservice operations
    Provides integration between the S3 microservice and Django models
    """
   
    def __init__(self):
        """Initialize the S3 service with Django settings"""
        self.client = None
        self._initialize_client()
   
    def _initialize_client(self):
        """Initialize the S3 client with Django database settings"""
        try:
            # Get database settings from Django
            db_settings = settings.DATABASES['default']
           
            mysql_config = {
                'host': db_settings.get('HOST', 'tprmintegration.c1womgmu83di.ap-south-1.rds.amazonaws.com'),
                'user': db_settings.get('USER', 'admin'),
                'password': db_settings.get('PASSWORD', 'rootroot'),
                'database': db_settings.get('NAME', 'tprm_integration'),
                'port': int(db_settings.get('PORT', 3306))
            }
           
            # Create the S3 client
            self.client = create_direct_mysql_client(mysql_config)
            print("SUCCESS: Django S3 Service initialized successfully")
           
        except Exception as e:
            print(f"ERROR: Failed to initialize S3 service: {str(e)}")
            # Fallback to client without MySQL
            try:
                self.client = RenderS3Client("http://15.207.1.40:3000", None)
                print("WARNING: S3 service initialized without MySQL tracking")
            except Exception as fallback_e:
                print(f"ERROR: Fallback initialization failed: {str(fallback_e)}")
                self.client = None
   
    def test_connection(self) -> Dict:
        """Test connection to S3 microservice and database"""
        if not self.client:
            return {
                'success': False,
                'error': 'S3 client not initialized'
            }
       
        return self.client.test_connection()
   
    def upload_file(self, file_path: str, user_id: str,
                   custom_file_name: Optional[str] = None,
                   rfp_id: Optional[int] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Upload a file to S3 and create Django model record
       
        Args:
            file_path: Path to the file to upload
            user_id: User ID for tracking
            custom_file_name: Custom name for the file
            rfp_id: Optional RFP ID for association
           
        Returns:
            Dict with success status and file information
        """
        if not self.client:
            return {
                'success': False,
                'error': 'S3 client not initialized'
            }
       
        try:
            # Upload to S3 via microservice first
            result = self.client.upload(file_path, user_id, custom_file_name)
           
            if result.get('success'):
                # Create Django model record with success data
                metadata_payload = {
                    'rfp_id': rfp_id,
                    'original_path': file_path,
                    's3_key': result['file_info']['s3Key'],
                    's3_bucket': result['file_info'].get('bucket', ''),
                    'stored_name': result['file_info']['storedName'],
                    'file_size': os.path.getsize(file_path),
                    's3_operation_id': result.get('operation_id'),
                    'upload_response': result['file_info'],
                    'platform': 'S3_Microservice'
                }
 
                if metadata and isinstance(metadata, dict):
                    metadata_payload.update(metadata)
 
                s3_file = S3Files.objects.create(
                    url=result['file_info']['url'],
                    file_type=os.path.splitext(file_path)[1][1:].lower() if '.' in file_path else '',
                    file_name=custom_file_name or os.path.basename(file_path),
                    user_id=user_id,
                    metadata=metadata_payload
                )
               
                return {
                    'success': True,
                    's3_file_id': s3_file.id,
                    's3_url': result['file_info']['url'],
                    's3_key': result['file_info']['s3Key'],
                    'stored_name': result['file_info']['storedName'],
                    'filename': custom_file_name or os.path.basename(file_path),
                    'file_size': os.path.getsize(file_path),
                    'document_url': result['file_info']['url'],
                    'message': 'File uploaded successfully'
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Upload failed')
                }
               
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Upload failed: {error_msg}")
           
            return {
                'success': False,
                'error': error_msg
            }
   
    def download_file(self, s3_key: str, file_name: str,
                     user_id: str, destination_path: str = "./downloads") -> Dict:
        """
        Download a file from S3 and create Django model record
       
        Args:
            s3_key: S3 key of the file to download
            file_name: Name for the downloaded file
            user_id: User ID for tracking
            destination_path: Local path to save the file
           
        Returns:
            Dict with success status and file information
        """
        if not self.client:
            return {
                'success': False,
                'error': 'S3 client not initialized'
            }
       
        try:
            # Create Django model record first
            file_storage = FileStorage.objects.create(
                operation_type='download',
                user_id=user_id,
                file_name=file_name,
                s3_key=s3_key,
                status='pending',
                metadata={
                    'destination_path': destination_path,
                    'platform': 'S3_Microservice'
                }
            )
           
            # Download from S3 via microservice
            result = self.client.download(s3_key, file_name, destination_path, user_id)
           
            if result.get('success'):
                # Update Django model with success
                file_storage.stored_name = os.path.basename(result['file_path'])
                file_storage.file_size = result.get('file_size')
                file_storage.status = 'completed'
                file_storage.completed_at = timezone.now()
                file_storage.metadata.update({
                    's3_operation_id': result.get('operation_id'),
                    'local_file_path': result['file_path'],
                    'download_response': result
                })
                file_storage.save()
               
                return {
                    'success': True,
                    'file_storage_id': file_storage.id,
                    'file_path': result['file_path'],
                    'file_size': result.get('file_size'),
                    'message': 'File downloaded successfully'
                }
            else:
                # Update Django model with failure
                file_storage.status = 'failed'
                file_storage.error = result.get('error', 'Unknown error')
                file_storage.save()
               
                return {
                    'success': False,
                    'file_storage_id': file_storage.id,
                    'error': result.get('error', 'Download failed')
                }
               
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Download failed: {error_msg}")
           
            # Update Django model with error if it exists
            if 'file_storage' in locals():
                file_storage.status = 'failed'
                file_storage.error = error_msg
                file_storage.save()
           
            return {
                'success': False,
                'error': error_msg
            }
   
    def export_data(self, data: Union[List[Dict], Dict], export_format: str,
                   file_name: str, user_id: str, rfp_id: Optional[int] = None) -> Dict:
        """
        Export data to S3 and create Django model record
       
        Args:
            data: Data to export
            export_format: Format for export (json, csv, xml, txt, pdf)
            file_name: Name for the exported file
            user_id: User ID for tracking
            rfp_id: Optional RFP ID for association
           
        Returns:
            Dict with success status and file information
        """
        if not self.client:
            return {
                'success': False,
                'error': 'S3 client not initialized'
            }
       
        try:
            record_count = len(data) if isinstance(data, list) else 1
           
            # Create Django model record first
            file_storage = FileStorage.objects.create(
                operation_type='export',
                user_id=user_id,
                file_name=file_name,
                export_format=export_format,
                record_count=record_count,
                status='pending',
                metadata={
                    'rfp_id': rfp_id,
                    'data_size': len(str(data)),
                    'platform': 'S3_Microservice'
                }
            )
           
            # Export via S3 microservice
            result = self.client.export(data, export_format, file_name, user_id)
           
            if result.get('success'):
                export_info = result.get('export_info', {})
               
                # Update Django model with success
                file_storage.stored_name = export_info.get('storedName', file_name)
                file_storage.s3_url = export_info.get('url', '')
                file_storage.s3_key = export_info.get('s3Key', '')
                file_storage.s3_bucket = export_info.get('bucket', '')
                file_storage.file_size = export_info.get('size', 0)
                file_storage.content_type = export_info.get('contentType', '')
                file_storage.status = 'completed'
                file_storage.completed_at = timezone.now()
                file_storage.metadata.update({
                    's3_operation_id': result.get('operation_id'),
                    'export_response': export_info
                })
                file_storage.save()
               
                return {
                    'success': True,
                    'file_storage_id': file_storage.id,
                    's3_url': export_info.get('url', ''),
                    's3_key': export_info.get('s3Key', ''),
                    'stored_name': export_info.get('storedName', file_name),
                    'file_size': export_info.get('size', 0),
                    'message': f'Data exported successfully as {export_format.upper()}'
                }
            else:
                # Update Django model with failure
                file_storage.status = 'failed'
                file_storage.error = result.get('error', 'Unknown error')
                file_storage.save()
               
                return {
                    'success': False,
                    'file_storage_id': file_storage.id,
                    'error': result.get('error', 'Export failed')
                }
               
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Export failed: {error_msg}")
           
            # Update Django model with error if it exists
            if 'file_storage' in locals():
                file_storage.status = 'failed'
                file_storage.error = error_msg
                file_storage.save()
           
            return {
                'success': False,
                'error': error_msg
            }
   
    def get_file_history(self, user_id: Optional[str] = None,
                        operation_type: Optional[str] = None,
                        limit: int = 10) -> List[Dict]:
        """
        Get file operation history from Django models
       
        Args:
            user_id: Filter by user ID
            operation_type: Filter by operation type
            limit: Maximum number of records to return
           
        Returns:
            List of file operation records
        """
        queryset = FileStorage.objects.all()
       
        if user_id:
            queryset = queryset.filter(user_id=user_id)
       
        if operation_type:
            queryset = queryset.filter(operation_type=operation_type)
       
        queryset = queryset.order_by('-created_at')[:limit]
       
        return [
            {
                'id': record.id,
                'operation_type': record.operation_type,
                'user_id': record.user_id,
                'file_name': record.file_name,
                'stored_name': record.stored_name,
                's3_url': record.s3_url,
                's3_key': record.s3_key,
                'file_type': record.file_type,
                'file_size': record.file_size,
                'export_format': record.export_format,
                'record_count': record.record_count,
                'status': record.status,
                'error': record.error,
                'metadata': record.metadata,
                'created_at': record.created_at.isoformat() if record.created_at else None,
                'updated_at': record.updated_at.isoformat() if record.updated_at else None,
                'completed_at': record.completed_at.isoformat() if record.completed_at else None,
            }
            for record in queryset
        ]
   
    def get_file_stats(self) -> Dict:
        """
        Get file operation statistics from Django models
       
        Returns:
            Dict with operation statistics
        """
        from django.db.models import Count, Sum, Avg
       
        stats = FileStorage.objects.aggregate(
            total_operations=Count('id'),
            completed_operations=Count('id', filter=models.Q(status='completed')),
            failed_operations=Count('id', filter=models.Q(status='failed')),
            total_file_size=Sum('file_size'),
            avg_file_size=Avg('file_size')
        )
       
        # Get operations by type
        operations_by_type = FileStorage.objects.values('operation_type').annotate(
            count=Count('id'),
            completed=Count('id', filter=models.Q(status='completed')),
            failed=Count('id', filter=models.Q(status='failed'))
        ).order_by('operation_type')
       
        # Get recent activity (last 7 days)
        from django.utils import timezone
        from datetime import timedelta
       
        recent_cutoff = timezone.now() - timedelta(days=7)
        recent_activity = FileStorage.objects.filter(
            created_at__gte=recent_cutoff
        ).extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            operations=Count('id')
        ).order_by('-date')
       
        return {
            'total_operations': stats['total_operations'] or 0,
            'completed_operations': stats['completed_operations'] or 0,
            'failed_operations': stats['failed_operations'] or 0,
            'total_file_size': stats['total_file_size'] or 0,
            'avg_file_size': stats['avg_file_size'] or 0,
            'operations_by_type': list(operations_by_type),
            'recent_activity': list(recent_activity)
        }
 
 
# Global service instance
s3_service = DjangoS3Service()
 
 
def get_s3_service() -> DjangoS3Service:
    """Get the global S3 service instance"""
    return s3_service
 
 