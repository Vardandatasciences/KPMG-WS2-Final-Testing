"""
Django management command for S3 operations
Provides command-line interface for S3 microservice operations
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import json
from typing import Dict, Any

from tprm_backend.rfp.s3_service import get_s3_service


class Command(BaseCommand):
    help = 'Perform S3 operations via microservice'
    
    def add_arguments(self, parser):
        # Subcommands
        subparsers = parser.add_subparsers(dest='operation', help='S3 operation to perform')
        
        # Health check
        health_parser = subparsers.add_parser('health', help='Check S3 service health')
        
        # Upload file
        upload_parser = subparsers.add_parser('upload', help='Upload file to S3')
        upload_parser.add_argument('file_path', help='Path to file to upload')
        upload_parser.add_argument('--user-id', default='admin', help='User ID for tracking')
        upload_parser.add_argument('--file-name', help='Custom file name')
        upload_parser.add_argument('--rfp-id', type=int, help='RFP ID for association')
        
        # Download file
        download_parser = subparsers.add_parser('download', help='Download file from S3')
        download_parser.add_argument('s3_key', help='S3 key of file to download')
        download_parser.add_argument('file_name', help='Name for downloaded file')
        download_parser.add_argument('--user-id', default='admin', help='User ID for tracking')
        download_parser.add_argument('--destination', default='./downloads', help='Download destination path')
        
        # Export data
        export_parser = subparsers.add_parser('export', help='Export data to S3')
        export_parser.add_argument('data_file', help='JSON file containing data to export')
        export_parser.add_argument('format', choices=['json', 'csv', 'xml', 'txt', 'pdf'], help='Export format')
        export_parser.add_argument('file_name', help='Name for exported file')
        export_parser.add_argument('--user-id', default='admin', help='User ID for tracking')
        export_parser.add_argument('--rfp-id', type=int, help='RFP ID for association')
        
        # Export RFP data
        export_rfp_parser = subparsers.add_parser('export-rfp', help='Export RFP data to S3')
        export_rfp_parser.add_argument('rfp_id', type=int, help='RFP ID to export')
        export_rfp_parser.add_argument('format', choices=['json', 'csv', 'xml', 'txt', 'pdf'], help='Export format')
        export_rfp_parser.add_argument('--file-name', help='Name for exported file')
        export_rfp_parser.add_argument('--user-id', default='admin', help='User ID for tracking')
        
        # History
        history_parser = subparsers.add_parser('history', help='Show file operation history')
        history_parser.add_argument('--user-id', help='Filter by user ID')
        history_parser.add_argument('--operation-type', choices=['upload', 'download', 'export'], help='Filter by operation type')
        history_parser.add_argument('--limit', type=int, default=10, help='Maximum number of records')
        
        # Stats
        stats_parser = subparsers.add_parser('stats', help='Show file operation statistics')
        
        # Test connection
        test_parser = subparsers.add_parser('test', help='Test S3 service connection')
    
    def handle(self, *args, **options):
        operation = options.get('operation')
        
        if not operation:
            self.stdout.write(self.style.ERROR('Please specify an operation. Use --help for available operations.'))
            return
        
        try:
            s3_service = get_s3_service()
            
            if operation == 'health':
                self.handle_health(s3_service)
            elif operation == 'upload':
                self.handle_upload(s3_service, options)
            elif operation == 'download':
                self.handle_download(s3_service, options)
            elif operation == 'export':
                self.handle_export(s3_service, options)
            elif operation == 'export-rfp':
                self.handle_export_rfp(s3_service, options)
            elif operation == 'history':
                self.handle_history(s3_service, options)
            elif operation == 'stats':
                self.handle_stats(s3_service)
            elif operation == 'test':
                self.handle_test(s3_service)
            else:
                self.stdout.write(self.style.ERROR(f'Unknown operation: {operation}'))
                
        except Exception as e:
            raise CommandError(f'S3 operation failed: {str(e)}')
    
    def handle_health(self, s3_service):
        """Handle health check operation"""
        self.stdout.write('🔍 Checking S3 service health...')
        
        result = s3_service.test_connection()
        
        if result.get('overall_success'):
            self.stdout.write(self.style.SUCCESS('✅ S3 service is healthy'))
            self.stdout.write(f'   Direct Status: {result.get("direct_status", "unknown")}')
            self.stdout.write(f'   MySQL Status: {result.get("mysql_status", "unknown")}')
        else:
            self.stdout.write(self.style.ERROR('❌ S3 service is unhealthy'))
            if result.get('direct_error'):
                self.stdout.write(f'   Direct Error: {result["direct_error"]}')
            if result.get('mysql_error'):
                self.stdout.write(f'   MySQL Error: {result["mysql_error"]}')
    
    def handle_upload(self, s3_service, options):
        """Handle file upload operation"""
        file_path = options['file_path']
        user_id = options['user_id']
        file_name = options.get('file_name')
        rfp_id = options.get('rfp_id')
        
        if not os.path.exists(file_path):
            raise CommandError(f'File not found: {file_path}')
        
        self.stdout.write(f'📤 Uploading {file_path}...')
        
        result = s3_service.upload_file(
            file_path=file_path,
            user_id=user_id,
            custom_file_name=file_name,
            rfp_id=rfp_id
        )
        
        if result.get('success'):
            self.stdout.write(self.style.SUCCESS('✅ Upload successful'))
            self.stdout.write(f'   File Storage ID: {result.get("file_storage_id")}')
            self.stdout.write(f'   S3 URL: {result.get("s3_url")}')
            self.stdout.write(f'   S3 Key: {result.get("s3_key")}')
            self.stdout.write(f'   Stored Name: {result.get("stored_name")}')
        else:
            self.stdout.write(self.style.ERROR(f'❌ Upload failed: {result.get("error")}'))
    
    def handle_download(self, s3_service, options):
        """Handle file download operation"""
        s3_key = options['s3_key']
        file_name = options['file_name']
        user_id = options['user_id']
        destination = options['destination']
        
        self.stdout.write(f'⬇️  Downloading {file_name} from S3...')
        
        result = s3_service.download_file(
            s3_key=s3_key,
            file_name=file_name,
            user_id=user_id,
            destination_path=destination
        )
        
        if result.get('success'):
            self.stdout.write(self.style.SUCCESS('✅ Download successful'))
            self.stdout.write(f'   File Storage ID: {result.get("file_storage_id")}')
            self.stdout.write(f'   Local Path: {result.get("file_path")}')
            self.stdout.write(f'   File Size: {result.get("file_size")} bytes')
        else:
            self.stdout.write(self.style.ERROR(f'❌ Download failed: {result.get("error")}'))
    
    def handle_export(self, s3_service, options):
        """Handle data export operation"""
        data_file = options['data_file']
        export_format = options['format']
        file_name = options['file_name']
        user_id = options['user_id']
        rfp_id = options.get('rfp_id')
        
        if not os.path.exists(data_file):
            raise CommandError(f'Data file not found: {data_file}')
        
        # Load data from JSON file
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        self.stdout.write(f'📊 Exporting data as {export_format.upper()}...')
        
        result = s3_service.export_data(
            data=data,
            export_format=export_format,
            file_name=file_name,
            user_id=user_id,
            rfp_id=rfp_id
        )
        
        if result.get('success'):
            self.stdout.write(self.style.SUCCESS('✅ Export successful'))
            self.stdout.write(f'   File Storage ID: {result.get("file_storage_id")}')
            self.stdout.write(f'   S3 URL: {result.get("s3_url")}')
            self.stdout.write(f'   S3 Key: {result.get("s3_key")}')
            self.stdout.write(f'   Stored Name: {result.get("stored_name")}')
            self.stdout.write(f'   File Size: {result.get("file_size")} bytes')
        else:
            self.stdout.write(self.style.ERROR(f'❌ Export failed: {result.get("error")}'))
    
    def handle_export_rfp(self, s3_service, options):
        """Handle RFP data export operation"""
        rfp_id = options['rfp_id']
        export_format = options['format']
        file_name = options.get('file_name', f'rfp_{rfp_id}_export')
        user_id = options['user_id']
        
        self.stdout.write(f'📊 Exporting RFP {rfp_id} as {export_format.upper()}...')
        
        # Get RFP data
        from rfp.models import RFP
        try:
            rfp = RFP.objects.get(rfp_id=rfp_id)
        except RFP.DoesNotExist:
            raise CommandError(f'RFP with ID {rfp_id} not found')
        
        # Prepare RFP data for export
        rfp_data = {
            'rfp_id': rfp.rfp_id,
            'rfp_number': rfp.rfp_number,
            'rfp_title': rfp.rfp_title,
            'description': rfp.description,
            'rfp_type': rfp.rfp_type,
            'category': rfp.category,
            'estimated_value': float(rfp.estimated_value) if rfp.estimated_value else None,
            'currency': rfp.currency,
            'status': rfp.status,
            'created_at': rfp.created_at.isoformat() if rfp.created_at else None,
            'updated_at': rfp.updated_at.isoformat() if rfp.updated_at else None,
            'submission_deadline': rfp.submission_deadline.isoformat() if rfp.submission_deadline else None,
            'evaluation_period_end': rfp.evaluation_period_end.isoformat() if rfp.evaluation_period_end else None,
            'award_date': rfp.award_date.isoformat() if rfp.award_date else None,
        }
        
        result = s3_service.export_data(
            data=rfp_data,
            export_format=export_format,
            file_name=file_name,
            user_id=user_id,
            rfp_id=rfp_id
        )
        
        if result.get('success'):
            self.stdout.write(self.style.SUCCESS('✅ RFP export successful'))
            self.stdout.write(f'   File Storage ID: {result.get("file_storage_id")}')
            self.stdout.write(f'   S3 URL: {result.get("s3_url")}')
            self.stdout.write(f'   S3 Key: {result.get("s3_key")}')
            self.stdout.write(f'   Stored Name: {result.get("stored_name")}')
            self.stdout.write(f'   File Size: {result.get("file_size")} bytes')
        else:
            self.stdout.write(self.style.ERROR(f'❌ RFP export failed: {result.get("error")}'))
    
    def handle_history(self, s3_service, options):
        """Handle history operation"""
        user_id = options.get('user_id')
        operation_type = options.get('operation_type')
        limit = options['limit']
        
        self.stdout.write('📋 File operation history:')
        
        history = s3_service.get_file_history(
            user_id=user_id,
            operation_type=operation_type,
            limit=limit
        )
        
        if not history:
            self.stdout.write('   No operations found')
            return
        
        for i, record in enumerate(history, 1):
            status_emoji = "✅" if record['status'] == 'completed' else "❌" if record['status'] == 'failed' else "⏳"
            self.stdout.write(f'   {i}. {status_emoji} {record["operation_type"]} - {record["file_name"]} ({record["status"]})')
            if record.get('s3_url'):
                self.stdout.write(f'      S3 URL: {record["s3_url"]}')
            if record.get('error'):
                self.stdout.write(f'      Error: {record["error"]}')
    
    def handle_stats(self, s3_service):
        """Handle stats operation"""
        self.stdout.write('📊 File operation statistics:')
        
        stats = s3_service.get_file_stats()
        
        self.stdout.write(f'   Total Operations: {stats.get("total_operations", 0)}')
        self.stdout.write(f'   Completed: {stats.get("completed_operations", 0)}')
        self.stdout.write(f'   Failed: {stats.get("failed_operations", 0)}')
        self.stdout.write(f'   Total File Size: {stats.get("total_file_size", 0)} bytes')
        self.stdout.write(f'   Average File Size: {stats.get("avg_file_size", 0):.2f} bytes')
        
        if stats.get('operations_by_type'):
            self.stdout.write('   Operations by type:')
            for op_stat in stats['operations_by_type']:
                self.stdout.write(f'     - {op_stat["operation_type"]}: {op_stat["count"]} total')
    
    def handle_test(self, s3_service):
        """Handle test connection operation"""
        self.stdout.write('🧪 Testing S3 service connection...')
        
        result = s3_service.test_connection()
        
        if result.get('overall_success'):
            self.stdout.write(self.style.SUCCESS('✅ All systems operational'))
            
            # Show operation stats
            stats = s3_service.get_file_stats()
            if stats:
                self.stdout.write(f'\n📊 Database Stats:')
                self.stdout.write(f'   Total operations: {stats.get("total_operations", 0)}')
                self.stdout.write(f'   Completed: {stats.get("completed_operations", 0)}')
                self.stdout.write(f'   Failed: {stats.get("failed_operations", 0)}')
        else:
            self.stdout.write(self.style.ERROR('❌ Some systems need attention'))
            if result.get('direct_error'):
                self.stdout.write(f'   Direct Error: {result["direct_error"]}')
            if result.get('mysql_error'):
                self.stdout.write(f'   MySQL Error: {result["mysql_error"]}')
