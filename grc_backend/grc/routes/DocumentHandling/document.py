from rest_framework.decorators import (
    api_view,
    parser_classes,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db.models import Q
from grc.models import (
    FileOperations,
    Users,
    CompanyFolder,
    CompanySubfolder,
    compute_retention_expiry,
    upsert_retention_timeline,
)
from datetime import datetime
import logging
import os
import tempfile
from grc.routes.Global.s3_fucntions import create_direct_mysql_client, RenderS3Client
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
import re

logger = logging.getLogger(__name__)

# Modules we never want to expose to the UI
EXCLUDED_MODULES = {'synthetic'}


def apply_module_exclusions(queryset):
    """
    Remove modules that should not surface in API responses.
    """
    for module_name in EXCLUDED_MODULES:
        queryset = queryset.exclude(module__iexact=module_name)
    return queryset


def get_user_display_name(user_id):
    """
    Get user display name from user_id
    Returns full name (FirstName LastName) or username as fallback
    """
    try:
        if not user_id:
            return 'Unknown User'
        
        # Try to get user by UserId (integer)
        try:
            user_id_int = int(user_id)
            user = Users.objects.get(UserId=user_id_int)
            if user.FirstName and user.LastName:
                return f"{user.FirstName} {user.LastName}"
            elif user.UserName:
                return user.UserName
            else:
                return f"User {user_id}"
        except (ValueError, Users.DoesNotExist):
            # If user_id is not an integer or user not found, try as username
            try:
                user = Users.objects.get(UserName=user_id)
                if user.FirstName and user.LastName:
                    return f"{user.FirstName} {user.LastName}"
                else:
                    return user.UserName
            except Users.DoesNotExist:
                return str(user_id)  # Return original user_id if not found
    except Exception as e:
        logger.warning(f"Error getting user name for {user_id}: {str(e)}")
        return str(user_id)


@api_view(['GET'])
def get_documents(request):
    """
    Fetch documents from FileOperations table with pagination
    Optionally filter by module: policy, audit, incident, risk
    """
    try:
        # Get query parameters
        module_filter = request.GET.get('module', 'all')
        search_query = request.GET.get('search', '')
        file_type_filter = request.GET.get('file_type', 'all')
        company_code = request.GET.get('company_code', '') or request.GET.get('company', '')
        subfolder_code = request.GET.get('subfolder_code', '') or request.GET.get('subfolder', '')
        
        # Pagination parameters
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
        except (ValueError, TypeError):
            page = 1
            page_size = 20
        
        # Ensure valid pagination values
        page = max(1, page)
        page_size = max(1, min(100, page_size))  # Limit page_size to 100
        
        # Base query - get all uploads (completed, pending, failed)
        # Exclude downloads, exports, and system-generated files
        queryset = FileOperations.objects.filter(
            operation_type='upload'
        ).exclude(
            user_id='export_user'  # Exclude system-generated exports
        )
        queryset = apply_module_exclusions(queryset)
        
        # Filter by module
        if module_filter and module_filter != 'all':
            queryset = queryset.filter(module__iexact=module_filter)
        
        # Search filter
        if search_query:
            queryset = queryset.filter(
                Q(file_name__icontains=search_query) |
                Q(original_name__icontains=search_query) |
                Q(user_id__icontains=search_query)
            )
        
        # File type filter
        if file_type_filter and file_type_filter != 'all':
            queryset = queryset.filter(file_type__iexact=file_type_filter)

        # Company filter - filename prefix company_ or company_subfolder_
        if company_code:
            try:
                company_prefix = sanitize_filename_part(company_code)
                if company_prefix and company_prefix != 'na':
                    if subfolder_code:
                        sub_prefix = sanitize_filename_part(subfolder_code)
                        if sub_prefix and sub_prefix != 'na':
                            queryset = queryset.filter(
                                file_name__istartswith=f"{company_prefix}_{sub_prefix}_"
                            )
                        else:
                            queryset = queryset.filter(file_name__istartswith=f"{company_prefix}_")
                    else:
                        queryset = queryset.filter(file_name__istartswith=f"{company_prefix}_")
            except Exception as prefix_exc:
                logger.warning(f"Error applying company_code filter '{company_code}': {prefix_exc}")
        
        # Order by most recent first
        queryset = queryset.order_by('-created_at')
        
        # Get total count before pagination
        total_count = queryset.count()
        
        # Calculate pagination
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        
        # Apply pagination
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_queryset = queryset[start_index:end_index]
        
        # Build response
        documents = []
        for file_op in paginated_queryset:
            # Determine file type from file_type or content_type
            file_ext = file_op.file_type or ''
            if not file_ext and file_op.content_type:
                # Extract extension from content_type
                if 'pdf' in file_op.content_type.lower():
                    file_ext = 'pdf'
                elif 'word' in file_op.content_type.lower() or 'document' in file_op.content_type.lower():
                    file_ext = 'doc'
                elif 'excel' in file_op.content_type.lower() or 'spreadsheet' in file_op.content_type.lower():
                    file_ext = 'xlsx'
                elif 'csv' in file_op.content_type.lower():
                    file_ext = 'csv'
                else:
                    file_ext = 'file'
            
            # Format file size
            file_size_str = format_file_size(file_op.file_size)
            
            # Get display name - try to get originalName from metadata.upload_response first
            display_name = file_op.file_name or 'Unknown File'
            
            # Try to extract originalName from metadata.upload_response
            if file_op.metadata:
                try:
                    import json
                    metadata = json.loads(file_op.metadata) if isinstance(file_op.metadata, str) else file_op.metadata
                    if metadata and 'upload_response' in metadata:
                        upload_response = metadata['upload_response']
                        if upload_response and 'originalName' in upload_response:
                            display_name = upload_response['originalName']
                            # logger.info(f"Using originalName from upload_response: {display_name}")
                        # else: No originalName found - use fallback, no need to log
                    # else: No upload_response in metadata - use fallback, no need to log
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Error parsing metadata for file {file_op.id}: {str(e)}")
            
            # If no originalName found, use original_name as fallback
            if display_name == file_op.file_name:
                display_name = file_op.original_name or file_op.file_name or 'Unknown File'
                # logger.info(f"Using fallback name: {display_name}")
            
            # Get user display name
            user_display_name = get_user_display_name(file_op.user_id)
            
            documents.append({
                'id': file_op.id,
                'name': display_name,
                'file_name': file_op.file_name or '',  # stored filename for company/subfolder filtering
                'fileType': file_ext.lower(),
                'fileSize': file_size_str,
                'uploadTime': file_op.created_at.isoformat() if file_op.created_at else None,
                'uploadedBy': user_display_name,
                'module': file_op.module or 'general',
                's3Url': file_op.s3_url or '',
                's3Key': file_op.s3_key or '',
                's3Bucket': file_op.s3_bucket or '',
                'description': f'{file_op.module or "General"} document uploaded on {file_op.created_at.strftime("%Y-%m-%d") if file_op.created_at else "unknown date"}',
                'status': file_op.status,
                'contentType': file_op.content_type or ''
            })
        
        return Response({
            'success': True,
            'count': len(documents),
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'documents': documents
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
            'documents': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_document_counts(request):
    """
    Get document counts by module
    """
    try:
        # Base query - all uploads (exclude downloads, exports, and system files)
        base_query = FileOperations.objects.filter(
            operation_type='upload'
        ).exclude(
            user_id='export_user'  # Exclude system-generated exports
        )
        base_query = apply_module_exclusions(base_query)
        
        counts = {
            'all': base_query.count(),
            'policy': base_query.filter(module__iexact='policy').count(),
            'audit': base_query.filter(module__iexact='audit').count(),
            'incident': base_query.filter(module__iexact='incident').count(),
            'risk': base_query.filter(module__iexact='risk').count(),
            'event': base_query.filter(module__iexact='event').count()
        }
        
        return Response({
            'success': True,
            'counts': counts
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching document counts: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
            'counts': {}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def format_file_size(size_in_bytes):
    """
    Format file size from bytes to human-readable format
    """
    if not size_in_bytes:
        return "Unknown size"
    
    size = float(size_in_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    
    return f"{size:.1f} PB"


@api_view(['GET'])
def get_document_download_url(request, doc_id: int):
    """
    Return a short-lived, read-only download URL for a document.

    - For new secure uploads: uses s3_bucket + s3_key and the S3 microservice (/presign-get).
    - For legacy records that still have s3_url: falls back to that URL.
    """
    try:
        try:
            file_op = FileOperations.objects.get(id=doc_id, operation_type='upload')
        except FileOperations.DoesNotExist:
            return Response(
                {"success": False, "error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Preferred: secure mode with bucket + key
        bucket = (file_op.s3_bucket or "").strip()
        key = (file_op.s3_key or "").strip()
        file_name = file_op.original_name or file_op.file_name or "document"
        disposition = request.GET.get("disposition", "attachment")

        if bucket and key:
            client = RenderS3Client()
            try:
                download_url = client.presign_get(
                    bucket=bucket,
                    key=key,
                    file_name=file_name,
                    expires_in=900,
                    disposition=disposition or "attachment",
                )
            except Exception as exc:
                logger.error(
                    f"Error generating presigned URL for document {doc_id}: {exc}",
                    exc_info=True,
                )
                return Response(
                    {
                        "success": False,
                        "error": "Failed to generate download link for this document",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {
                    "success": True,
                    "downloadUrl": download_url,
                    "legacy": False,
                },
                status=status.HTTP_200_OK,
            )

        # Legacy fallback: use stored s3_url if present
        if file_op.s3_url:
            return Response(
                {
                    "success": True,
                    "downloadUrl": file_op.s3_url,
                    "legacy": True,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "error": "No S3 location stored for this document",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as exc:
        logger.error(f"Error in get_document_download_url for {doc_id}: {exc}", exc_info=True)
        return Response(
            {
                "success": False,
                "error": "Unexpected error while generating download link",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def sanitize_filename_part(value: str) -> str:
    """
    Sanitize a string so it is safe to use as part of a filename.
    Converts to lowercase, replaces non-alphanumeric characters with underscores,
    and trims redundant underscores.
    """
    if not value:
        return 'na'
    
    value = value.strip().lower()
    value = re.sub(r'[^a-z0-9]+', '_', value)
    value = value.strip('_')
    return value or 'na'


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def list_company_folders(request):
    """
    List all active company folders for the current tenant (if available).
    """
    try:
        queryset = CompanyFolder.objects.filter(is_active=True).order_by('name')

        # If the model has tenant information and a current tenant is set,
        # filter by tenant. We avoid hard dependency on tenant context here.
        if hasattr(CompanyFolder, 'tenant'):
            from grc.tenant_context import get_current_tenant

            tenant_id = get_current_tenant()
            if tenant_id:
                queryset = queryset.filter(tenant__tenant_id=tenant_id)

        folders = []
        for folder in queryset:
            # Count documents in this company folder (file_name starts with code_)
            prefix = f"{sanitize_filename_part(folder.code)}_"
            doc_count = FileOperations.objects.filter(
                operation_type='upload'
            ).exclude(user_id='export_user').filter(
                file_name__istartswith=prefix
            ).count()
            folders.append({
                'id': folder.folder_id,
                'name': folder.name,
                'code': folder.code,
                'description': folder.description or '',
                'document_count': doc_count,
            })

        return Response(
            {
                'success': True,
                'folders': folders,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as exc:
        logger.error(f"Error listing company folders: {exc}", exc_info=True)
        return Response(
            {
                'success': False,
                'error': str(exc),
                'folders': [],
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def create_company_folder(request):
    """
    Create a new company folder.
    """
    try:
        name = (request.data.get('name') or '').strip()
        description = (request.data.get('description') or '').strip()

        if not name:
            return Response(
                {
                    'success': False,
                    'error': 'Name is required',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        code = sanitize_filename_part(name)

        # Ensure code is unique
        existing = CompanyFolder.objects.filter(code__iexact=code).first()
        if existing:
            return Response(
                {
                    'success': False,
                    'error': 'A company folder with this name already exists',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        folder = CompanyFolder(
            name=name,
            code=code,
            description=description or None,
            is_active=True,
        )

        # Best-effort: set created_by from authenticated user if available
        try:
            if hasattr(request, 'user') and getattr(request.user, 'id', None):
                # Map Django auth user to grc.Users if possible
                user = Users.objects.filter(UserId=getattr(request.user, 'id')).first()
                if user:
                    folder.created_by = user
                    folder.updated_by = user
        except Exception as map_exc:
            logger.warning(f"Could not map request.user to Users: {map_exc}")

        folder.save()

        return Response(
            {
                'success': True,
                'folder': {
                    'id': folder.folder_id,
                    'name': folder.name,
                    'code': folder.code,
                    'description': folder.description or '',
                },
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as exc:
        logger.error(f"Error creating company folder: {exc}", exc_info=True)
        return Response(
            {
                'success': False,
                'error': str(exc),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def list_company_subfolders(request, folder_id):
    """
    List subfolders for a company folder. Returns id, name, code, document_count.
    """
    try:
        company_folder = CompanyFolder.objects.filter(
            folder_id=folder_id, is_active=True
        ).first()
        if not company_folder:
            return Response(
                {'success': False, 'error': 'Company folder not found', 'subfolders': []},
                status=status.HTTP_404_NOT_FOUND,
            )
        queryset = CompanySubfolder.objects.filter(
            company_folder_id=folder_id, is_active=True
        ).order_by('name')
        company_prefix = f"{sanitize_filename_part(company_folder.code)}_"
        subfolders = []
        for sub in queryset:
            prefix = f"{company_prefix}{sanitize_filename_part(sub.code)}_"
            doc_count = FileOperations.objects.filter(
                operation_type='upload'
            ).exclude(user_id='export_user').filter(
                file_name__istartswith=prefix
            ).count()
            subfolders.append({
                'id': sub.subfolder_id,
                'name': sub.name,
                'code': sub.code,
                'document_count': doc_count,
            })
        return Response(
            {'success': True, 'subfolders': subfolders},
            status=status.HTTP_200_OK,
        )
    except Exception as exc:
        logger.error(f"Error listing company subfolders: {exc}", exc_info=True)
        return Response(
            {'success': False, 'error': str(exc), 'subfolders': []},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def create_company_subfolder(request, folder_id):
    """
    Create a subfolder inside a company folder.
    """
    try:
        company_folder = CompanyFolder.objects.filter(
            folder_id=folder_id, is_active=True
        ).first()
        if not company_folder:
            return Response(
                {'success': False, 'error': 'Company folder not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        name = (request.data.get('name') or '').strip()
        if not name:
            return Response(
                {'success': False, 'error': 'Name is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        code = sanitize_filename_part(name)
        existing = CompanySubfolder.objects.filter(
            company_folder_id=folder_id, code__iexact=code
        ).first()
        if existing:
            return Response(
                {'success': False, 'error': 'A folder with this name already exists in this company'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subfolder = CompanySubfolder(
            company_folder=company_folder,
            name=name,
            code=code,
            is_active=True,
        )
        subfolder.save()
        return Response(
            {
                'success': True,
                'subfolder': {
                    'id': subfolder.subfolder_id,
                    'name': subfolder.name,
                    'code': subfolder.code,
                },
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as exc:
        logger.error(f"Error creating company subfolder: {exc}", exc_info=True)
        return Response(
            {'success': False, 'error': str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_document(request):
    """
    Upload document with optional framework selection
    Naming convention: framework_module_datetime.filetype (if framework selected)
    Or: module_datetime.filetype (if no framework)
    """
    try:
        # Get form data
        uploaded_file = request.FILES.get('file')
        module = request.data.get('module')
        framework = request.data.get('framework', '')
        # Optional company code and subfolder (from company folders dropdown)
        company_code = request.data.get('company', '') or request.data.get('company_code', '')
        subfolder_code = request.data.get('subfolder', '') or request.data.get('subfolder_code', '')
        user_id = request.data.get('user_id', 'unknown-user')
        
        # Validation
        if not uploaded_file:
            return Response({
                'success': False,
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not module:
            return Response({
                'success': False,
                'error': 'Module is required'
            }, status=status.HTTP_400_BAD_REQUEST)
           # Convert framework name to framework_id if framework is provided
        framework_id = None
        if framework:
            try:
                from ...models import Framework
                # Try to find framework by name
                framework_obj = Framework.objects.filter(FrameworkName=framework).first()
                if framework_obj:
                    framework_id = framework_obj.FrameworkId
                    logger.info(f"✅ Found framework_id {framework_id} for framework '{framework}'")
                else:
                    logger.warning(f"⚠️ Framework '{framework}' not found in database")
            except Exception as e:
                logger.warning(f"⚠️ Error looking up framework '{framework}': {str(e)}")
 
        # Get file extension
        original_filename = uploaded_file.name
        file_extension = os.path.splitext(original_filename)[1]  # includes the dot
        
        # Generate timestamp
        timestamp = datetime.now()
        date_part = timestamp.strftime('%Y%m%d')
        
        # Sanitize parts for filename
        base_prefix = 'document_handling'
        company_part = sanitize_filename_part(company_code) if company_code else 'no_company'
        subfolder_part = sanitize_filename_part(subfolder_code) if subfolder_code else None
        framework_part = sanitize_filename_part(framework) if framework else 'no_framework'
        module_part = sanitize_filename_part(module)
        original_base = os.path.splitext(original_filename)[0]
        original_part = sanitize_filename_part(original_base)
        extension_part = file_extension.lower()
        
        # Naming: company_[subfolder_]framework_module_document_handling_date_original.ext
        filename_parts = [company_part]
        if subfolder_part:
            filename_parts.append(subfolder_part)
        filename_parts.extend([framework_part, module_part, base_prefix, date_part, original_part])
        custom_filename = f"{'_'.join(filename_parts)}{extension_part}"
        
        # logger.info(f"📤 Uploading document: {original_filename} -> {custom_filename}")
        # logger.info(f"   Module: {module}")
        # logger.info(f"   Framework: {framework or 'None'}")
        # logger.info(f"   User: {user_id}")
        
        # Save uploaded file temporarily
        temp_file_path = None
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                # Write uploaded file content to temp file
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            # logger.info(f"📁 Temporary file created: {temp_file_path}")
            
            # Create S3 client
            s3_client = create_direct_mysql_client()
            
            # Upload to S3 with custom filename
            upload_result = s3_client.upload(
                file_path=temp_file_path,
                user_id=user_id,
                custom_file_name=custom_filename,
                module=module,
                framework_id=framework_id
            )
            
            if upload_result.get('success'):
                # logger.info(f"✅ Upload successful: {upload_result.get('file_info', {}).get('storedName')}")
                
                operation_id = upload_result.get('operation_id')

                # Update FileOperations record to reflect custom filename
                if operation_id:
                    try:
                        # Load operation, update filename and apply retention
                        file_op = FileOperations.objects.get(id=operation_id)
                        file_op.file_name = custom_filename
                        file_op.original_name = custom_filename
                        if framework_id:
                            from ...models import Framework
                            try:
                                framework_obj = Framework.objects.get(FrameworkId=framework_id)
                                file_op.FrameworkId = framework_obj
                                logger.info(f"✅ Set FrameworkId {framework_id} for operation {operation_id}")
                            except Framework.DoesNotExist:
                                logger.warning(f"⚠️ Framework with ID {framework_id} not found")
 
 

                        # Compute and set retention expiry based on configuration
                        expiry_date = compute_retention_expiry('document_handling', 'document_upload')
                        if expiry_date:
                            file_op.retentionExpiry = expiry_date
                            update_fields = ['file_name', 'original_name', 'retentionExpiry']
                        if framework_id:
                            update_fields.append('FrameworkId')
                        file_op.save(update_fields=update_fields)
 
                        # Always attempt to upsert a retention timeline; helper
                        # will no-op if retentionExpiry is not set.
                        # Do not depend on FrameworkId here; helper will
                        # fall back to the default framework if needed.
                        upsert_retention_timeline(
                            file_op,
                            'file_operations',
                            record_name=file_op.display_name,
                            created_date=file_op.created_at,
                        )
                        # logger.info(f"📝 FileOperations record {operation_id} updated with filename and retention timeline")
                    except Exception as db_err:
                        logger.warning(f"⚠️ Failed to update FileOperations record {operation_id}: {db_err}")
                
                return Response({
                    'success': True,
                    'message': 'Document uploaded successfully',
                    'stored_name': upload_result.get('file_info', {}).get('storedName'),
                    'original_name': custom_filename,
                    'custom_name': custom_filename,
                    's3_url': upload_result.get('file_info', {}).get('url'),
                    's3_key': upload_result.get('file_info', {}).get('s3Key'),
                    'operation_id': operation_id,
                    'file_size': upload_result.get('file_info', {}).get('size'),
                    'module': module,
                    'framework': framework or None
                }, status=status.HTTP_200_OK)
            else:
                error_msg = upload_result.get('error', 'Unknown error during upload')
                logger.error(f"❌ Upload failed: {error_msg}")
                return Response({
                    'success': False,
                    'error': error_msg
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    # logger.info(f"🗑️  Temporary file deleted: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to delete temporary file: {str(e)}")
    
    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)