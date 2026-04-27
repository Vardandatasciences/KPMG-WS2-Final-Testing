from rest_framework.decorators import (
    api_view,
    parser_classes,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from django.db.models import Q
from grc.models import (
    FileOperations,
    Users,
    CompanyFolder,
    CompanySubfolder,
    CompanySubfolderDocument,
    compute_retention_expiry,
    upsert_retention_timeline,
)
from grc.rbac.utils import RBACUtils
from datetime import datetime
import logging
import os
import tempfile
from pathlib import Path
from grc.routes.Global.s3_fucntions import create_direct_mysql_client, RenderS3Client
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_protect as csrf_exempt
from grc.utils.auto_decrypt_helper import decrypt_any_encrypted_value
from grc.utils.data_encryption import GCM_ENVELOPE_PREFIX
from grc.utils.safe_paths import (
    safe_join,
    resolved_path_under_base,
    safe_upload_filename,
    UnsafePathError,
)
import re

logger = logging.getLogger(__name__)
CLIENT_SAFE_ERROR = "An internal error occurred. Please try again later."
MAX_SEARCH_LENGTH = 256
ALLOWED_MODULE_FILTERS = {'all', 'policy', 'audit', 'incident', 'risk', 'event', 'document_handling'}
ALLOWED_UPLOAD_MODULES = {'policy', 'audit', 'incident', 'risk', 'event', 'document_handling'}
ALLOWED_FILE_TYPE_FILTERS = {'all', 'pdf', 'doc', 'docx', 'xlsx', 'xls', 'csv', 'txt'}
ALLOWED_DISPOSITIONS = {'attachment', 'inline'}

# Never send raw encrypted blobs to the UI; if decryption failed, show this instead
ENCRYPTED_PLACEHOLDER = '—'

# Modules we never want to expose to the UI
EXCLUDED_MODULES = {'synthetic'}


def _get_authenticated_user(request):
    """Resolve authenticated GRC user from request context."""
    raw_request = getattr(request, '_request', request)
    grc_user = getattr(raw_request, '_grc_user', None)
    if grc_user and hasattr(grc_user, 'UserId'):
        try:
            return Users.objects.filter(UserId=int(grc_user.UserId)).first()
        except Exception:
            return None

    resolved_user_id = RBACUtils.get_user_id_from_request(request)
    if not resolved_user_id:
        return None
    try:
        return Users.objects.filter(UserId=int(resolved_user_id)).first()
    except Exception:
        return None


def _is_system_admin(user):
    try:
        return bool(user and RBACUtils.is_system_admin(int(user.UserId)))
    except Exception:
        return False


def _scope_file_operations_queryset(queryset, user, is_admin=False):
    """Scope FileOperations to authorized tenant/framework/user context."""
    if not user:
        return queryset.none()

    # Tenant boundary first when available on model + user.
    if hasattr(FileOperations, 'tenant_id') and getattr(user, 'tenant_id', None):
        queryset = queryset.filter(tenant_id=user.tenant_id)

    # Admin can view tenant-scoped records.
    if is_admin:
        return queryset

    user_id_str = str(user.UserId)
    user_framework_id = getattr(user, 'FrameworkId_id', None)
    if user_framework_id:
        return queryset.filter(Q(user_id=user_id_str) | Q(FrameworkId_id=user_framework_id))
    return queryset.filter(user_id=user_id_str)


def _can_access_file_operation(file_op, user, is_admin=False):
    if not user or not file_op:
        return False

    # Tenant isolation.
    if hasattr(file_op, 'tenant_id') and getattr(user, 'tenant_id', None):
        if file_op.tenant_id and file_op.tenant_id != user.tenant_id:
            return False

    if is_admin:
        return True

    if str(file_op.user_id or '') == str(user.UserId):
        return True

    user_framework_id = getattr(user, 'FrameworkId_id', None)
    file_framework_id = getattr(file_op, 'FrameworkId_id', None)
    return bool(user_framework_id and file_framework_id and int(user_framework_id) == int(file_framework_id))


def _get_approved_temp_upload_dir():
    """
    Return an approved temp upload directory under BASE_DIR/tmp/document_uploads.
    Uses centralized safe path helpers to enforce normalized boundary checks.
    """
    approved_path = safe_join(settings.BASE_DIR, "tmp", "document_uploads")
    Path(approved_path).mkdir(parents=True, exist_ok=True)
    if not resolved_path_under_base(approved_path, settings.BASE_DIR):
        raise UnsafePathError("Upload temp path is outside approved base directory")
    return approved_path


def _safe_for_display(value):
    """If value still looks like encrypted data after decryption, return placeholder."""
    if value is None or not isinstance(value, str):
        return value
    s = value.strip()
    if len(s) < 20:
        return value
    # Fernet tokens start with gAAAAA; AES-GCM field blobs use GRCv2$ prefix
    if s.startswith(GCM_ENVELOPE_PREFIX):
        return ENCRYPTED_PLACEHOLDER
    lower = s.lower()
    if lower.startswith('gaaaaa') or (len(s) >= 6 and lower[1:6] == 'aaaaa'):
        return ENCRYPTED_PLACEHOLDER
    return value


def _sanitize_text_output(value, max_len: int = 512):
    """
    Normalize text output for JSON/HTML rendering contexts.
    - Remove control characters
    - Trim excessive length
    - Neutralize CSV formula prefixes to reduce spreadsheet injection risk
    """
    if value is None:
        return value
    if not isinstance(value, str):
        value = str(value)

    cleaned = ''.join(ch for ch in value if ch == '\t' or ch == '\n' or ord(ch) >= 32)
    cleaned = cleaned.strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len]
    if cleaned.startswith(('=', '+', '-', '@')):
        cleaned = "'" + cleaned
    return cleaned


def _sanitize_folder_name(value: str) -> str:
    if not isinstance(value, str):
        return ''
    normalized = value.strip()
    if not normalized:
        return ''
    if len(normalized) > 120:
        return ''
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _\-.]{0,119}", normalized):
        return ''
    return normalized


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
    Returns username (UserName) when available, otherwise full name / raw id
    """
    try:
        if not user_id:
            return 'Unknown User'
        
        # Try to get user by UserId (integer)
        try:
            user_id_int = int(user_id)
            user = Users.objects.get(UserId=user_id_int)
            # Prefer username for display across the app
            if user.UserName:
                return user.UserName
            elif user.FirstName and user.LastName:
                return f"{user.FirstName} {user.LastName}"
            else:
                return f"User {user_id}"
        except (ValueError, Users.DoesNotExist):
            # If user_id is not an integer or user not found, try as username
            try:
                user = Users.objects.get(UserName=user_id)
                # Again, prefer username; fall back to full name if needed
                if user.UserName:
                    return user.UserName
                elif user.FirstName and user.LastName:
                    return f"{user.FirstName} {user.LastName}"
                else:
                    return str(user_id)
            except Users.DoesNotExist:
                return str(user_id)  # Return original user_id if not found
    except Exception as e:
        logger.warning(f"Error getting user name for {user_id}: {str(e)}")
        return str(user_id)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_documents(request):
    """
    Fetch documents from FileOperations table with pagination
    Optionally filter by module: policy, audit, incident, risk
    """
    current_user = _get_authenticated_user(request)
    if not current_user:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    is_admin = _is_system_admin(current_user)
    try:
        # Get query parameters
        module_filter = (request.GET.get('module', 'all') or 'all').strip().lower()
        search_query = (request.GET.get('search', '') or '').strip()
        file_type_filter = (request.GET.get('file_type', 'all') or 'all').strip().lower()
        company_code = (request.GET.get('company_code', '') or request.GET.get('company', '') or '').strip()
        subfolder_code = (request.GET.get('subfolder_code', '') or request.GET.get('subfolder', '') or '').strip()

        if module_filter not in ALLOWED_MODULE_FILTERS:
            return Response({'success': False, 'error': 'Invalid module filter'}, status=status.HTTP_400_BAD_REQUEST)
        if file_type_filter not in ALLOWED_FILE_TYPE_FILTERS:
            return Response({'success': False, 'error': 'Invalid file type filter'}, status=status.HTTP_400_BAD_REQUEST)
        if len(search_query) > MAX_SEARCH_LENGTH:
            return Response({'success': False, 'error': 'Search query too long'}, status=status.HTTP_400_BAD_REQUEST)
        if company_code and not _is_safe_lookup_code(company_code):
            return Response({'success': False, 'error': 'Invalid company code format'}, status=status.HTTP_400_BAD_REQUEST)
        if subfolder_code and not _is_safe_lookup_code(subfolder_code):
            return Response({'success': False, 'error': 'Invalid subfolder code format'}, status=status.HTTP_400_BAD_REQUEST)
        
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
        queryset = _scope_file_operations_queryset(queryset, current_user, is_admin=is_admin)
        
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

        # Company filter - filename prefix company_ or company_subfolder_, OR linked via CompanySubfolderDocument
        if company_code:
            try:
                resolved_folder, resolved_subfolder = _resolve_and_authorize_company_scope(
                    current_user, company_code=company_code, subfolder_code=subfolder_code
                )
                company_prefix = sanitize_filename_part(company_code)
                if company_prefix and company_prefix != 'na':
                    linked_file_op_ids = []
                    if subfolder_code:
                        sub_prefix = sanitize_filename_part(subfolder_code)
                        if sub_prefix and sub_prefix != 'na':
                            # Include docs whose file_name has the prefix (legacy) OR that are linked to this subfolder (e.g. AI audit evidence)
                            if resolved_subfolder:
                                linked_file_op_ids = list(
                                    CompanySubfolderDocument.objects.filter(
                                        company_subfolder=resolved_subfolder
                                    ).values_list('file_operation_id', flat=True)
                                )
                            if linked_file_op_ids:
                                queryset = queryset.filter(
                                    Q(file_name__istartswith=f"{company_prefix}_{sub_prefix}_") | Q(id__in=linked_file_op_ids)
                                )
                            else:
                                queryset = queryset.filter(
                                    file_name__istartswith=f"{company_prefix}_{sub_prefix}_"
                                )
                        else:
                            queryset = queryset.filter(file_name__istartswith=f"{company_prefix}_")
                    else:
                        # No subfolder selected: include prefix-based docs and docs linked to any subfolder (e.g. AI audit evidence)
                        if resolved_folder:
                            linked_file_op_ids = list(
                                CompanySubfolderDocument.objects.filter(
                                    company_subfolder__company_folder=resolved_folder
                                ).values_list('file_operation_id', flat=True)
                            )
                            if linked_file_op_ids:
                                queryset = queryset.filter(
                                    Q(file_name__istartswith=f"{company_prefix}_") | Q(id__in=linked_file_op_ids)
                                )
                            else:
                                queryset = queryset.filter(file_name__istartswith=f"{company_prefix}_")
                        else:
                            queryset = queryset.filter(file_name__istartswith=f"{company_prefix}_")
            except (ValueError, PermissionError):
                return Response({'success': False, 'error': 'Invalid company/subfolder scope'}, status=status.HTTP_400_BAD_REQUEST)
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

            # Raw stored_name from Direct/S3 (already a safe filename, not encrypted)
            stored_name_raw = getattr(file_op, 'stored_name', '') or ''
            stored_file_name = stored_name_raw or (file_op.file_name or '')
            if stored_file_name and stored_file_name != stored_name_raw and isinstance(stored_file_name, str):
                # Only attempt decryption when we're falling back to file_name
                stored_file_name = decrypt_any_encrypted_value(stored_file_name) or stored_file_name

            # For AI audit evidence pushed into Document Handling, prefer the stored filename
            # (which includes uploader name and audit context) so users can see who uploaded it.
            module_upper = (file_op.module or '').upper()
            if module_upper == 'DOCUMENT_HANDLING' and isinstance(stored_file_name, str):
                # If stored name comes from AI audit pipeline (contains 'ai_audit_') OR
                # the current display name still looks like encrypted noise, use stored_name.
                looks_encrypted = isinstance(display_name, str) and display_name.lower().startswith('gaaaaa')
                if 'ai_audit_' in stored_file_name or looks_encrypted:
                    display_name = stored_file_name

            # Never send raw encrypted text to UI (for any remaining cases)
            if isinstance(display_name, str):
                display_name = decrypt_any_encrypted_value(display_name) or display_name

            # Get user display name
            user_display_name = get_user_display_name(file_op.user_id)
            safe_display_name = _sanitize_text_output(_safe_for_display(display_name), max_len=255)
            safe_stored_name = _sanitize_text_output(_safe_for_display(stored_file_name), max_len=255)
            safe_uploaded_by = _sanitize_text_output(user_display_name, max_len=120)
            safe_module_name = _sanitize_text_output(file_op.module or 'general', max_len=64)
            safe_status = _sanitize_text_output(file_op.status or '', max_len=64)
            safe_content_type = _sanitize_text_output(file_op.content_type or '', max_len=120)
            
            documents.append({
                'id': file_op.id,
                'name': safe_display_name,
                'file_name': safe_stored_name,  # stored filename for company/subfolder filtering (decrypted for display)
                'fileType': file_ext.lower(),
                'fileSize': file_size_str,
                'uploadTime': file_op.created_at.isoformat() if file_op.created_at else None,
                'uploadedBy': safe_uploaded_by,
                'module': safe_module_name,
                # s3Url intentionally omitted — use /api/documents/<id>/download-url/ for a short-lived signed URL
                's3Url': '',
                's3Key': '',
                's3Bucket': '',
                'description': _sanitize_text_output(
                    f'{file_op.module or "General"} document uploaded on {file_op.created_at.strftime("%Y-%m-%d") if file_op.created_at else "unknown date"}',
                    max_len=256,
                ),
                'status': safe_status,
                'contentType': safe_content_type
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
            'error': CLIENT_SAFE_ERROR,
            'documents': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_document_counts(request):
    """
    Get document counts by module
    """
    current_user = _get_authenticated_user(request)
    if not current_user:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    is_admin = _is_system_admin(current_user)
    try:
        # Base query - all uploads (exclude downloads, exports, and system files)
        base_query = FileOperations.objects.filter(
            operation_type='upload'
        ).exclude(
            user_id='export_user'  # Exclude system-generated exports
        )
        base_query = apply_module_exclusions(base_query)
        base_query = _scope_file_operations_queryset(base_query, current_user, is_admin=is_admin)
        
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
            'error': CLIENT_SAFE_ERROR,
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


@csrf_exempt
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_document(request, doc_id: int):
    """
    Delete a single FileOperations upload record and its company-folder link.
    Safety rules:
    - If this file is linked as AI audit evidence for audits that are
      Work In Progress / Under review / Completed, deletion is blocked.
    """
    try:
        current_user = _get_authenticated_user(request)
        if not current_user:
            return Response({"success": False, "error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        is_admin = _is_system_admin(current_user)

        from grc.models import CompanySubfolderDocument, CompanySubfolder, CompanyFolder

        try:
            file_op = FileOperations.objects.get(id=doc_id, operation_type='upload')
        except FileOperations.DoesNotExist:
            return Response(
                {"success": False, "error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not _can_access_file_operation(file_op, current_user, is_admin=is_admin):
            return Response(
                {"success": False, "error": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # First, try to infer audit status from the company folder code.
        # AI Audit Evidence folders are created with code that includes the audit id
        # (e.g. "<sanitized_title>_<AuditId>"). If we can parse an AuditId from the
        # folder code and that audit is in a protected status, we block deletion.
        blocking_audits = set()
        try:
            link = CompanySubfolderDocument.objects.filter(file_operation=file_op).select_related(
                "company_subfolder__company_folder"
            ).first()
            if link and getattr(link, "company_subfolder", None):
                subfolder = link.company_subfolder
                folder = getattr(subfolder, "company_folder", None)
                if folder and folder.code:
                    parts = str(folder.code).rsplit("_", 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        inferred_audit_id = int(parts[1])
                        with create_direct_mysql_client() as conn:
                            cur = conn.cursor()
                            cur.execute(
                                "SELECT Status FROM audit WHERE AuditId = %s",
                                [inferred_audit_id],
                            )
                            row = cur.fetchone()
                            status_val = row[0] if row else None
                            if status_val in ("Work In Progress", "Under review", "Completed"):
                                blocking_audits.add((inferred_audit_id, status_val))
        except Exception:
            # If folder-based inference fails, fall back to ai_audit_data linkage only.
            pass

        # Also check if this file is used as AI audit evidence via direct linkage
        blocking_audits = set()
        try:
            with create_direct_mysql_client() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT DISTINCT a.AuditId, a.Status
                    FROM ai_audit_data d
                    JOIN audit a ON d.audit_id = a.AuditId
                    WHERE d.file_operation_id = %s
                    """,
                    [file_op.id],
                )
                for audit_id, status_val in cur.fetchall():
                    if status_val in ("Work In Progress", "Under review", "Completed"):
                        blocking_audits.add((audit_id, status_val))
        except Exception:
            # If this lookup fails, we don't block based on AI audits here;
            # ai_audit_api delete still enforces its own status rules.
            blocking_audits = set()

        if blocking_audits:
            return Response(
                {
                    "success": False,
                    "error": "This document is used as evidence for audits that are in progress or completed and "
                             "cannot be deleted from Document Handling.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Remove any company-folder link
        CompanySubfolderDocument.objects.filter(file_operation=file_op).delete()

        # Finally delete the FileOperations row itself
        file_op.delete()
        logger.info(
            "Document deleted: doc_id=%s actor_user_id=%s",
            doc_id,
            getattr(current_user, 'UserId', None),
        )

        return Response(
            {"success": True, "message": "Document deleted successfully"},
            status=status.HTTP_200_OK,
        )
    except Exception as exc:
        logger.error(f"Error deleting document {doc_id}: {exc}", exc_info=True)
        return Response(
            {"success": False, "error": CLIENT_SAFE_ERROR},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_document_download_url(request, doc_id: int):
    """
    Return a short-lived, read-only download URL for a document.

    - For new secure uploads: uses s3_bucket + s3_key and the S3 microservice (/presign-get).
    - Legacy direct `s3_url` values are not exposed by this endpoint.
    """
    try:
        current_user = _get_authenticated_user(request)
        if not current_user:
            return Response({"success": False, "error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        is_admin = _is_system_admin(current_user)

        try:
            file_op = FileOperations.objects.get(id=doc_id, operation_type='upload')
        except FileOperations.DoesNotExist:
            return Response(
                {"success": False, "error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not _can_access_file_operation(file_op, current_user, is_admin=is_admin):
            return Response(
                {"success": False, "error": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Preferred: secure mode with S3 key. Try multiple candidates so we match how Direct stored the object.
        bucket = (file_op.s3_bucket or "").strip()
        key = (file_op.s3_key or "").strip()
        stored_name = (file_op.stored_name or "").strip() if hasattr(file_op, "stored_name") else ""
        file_name = safe_upload_filename(file_op.original_name or file_op.file_name or "document")
        disposition = (request.GET.get("disposition", "attachment") or "attachment").strip().lower()
        if disposition not in ALLOWED_DISPOSITIONS:
            disposition = "attachment"

        # Build candidate keys: s3_key, stored_name, and their basenames
        candidates = []
        for val in (key, stored_name):
            if val and val not in candidates:
                candidates.append(val)
            if val and "/" in val:
                base = val.split("/")[-1]
                if base and base not in candidates:
                    candidates.append(base)

        if candidates:
            client = RenderS3Client()
            last_error = None
            for candidate_key in candidates:
                try:
                    # Direct microservice uses only the key; bucket is implicit in its config
                    download_url = client.get_presigned_download_url(candidate_key, file_name)
                    if download_url:
                        return Response(
                            {
                                "success": True,
                                "downloadUrl": download_url,
                                "legacy": False,
                            },
                            status=status.HTTP_200_OK,
                        )
                except Exception as exc:
                    last_error = exc
                    logger.error(
                        f"Error generating presigned URL for document {doc_id} with key '{candidate_key}': {exc}",
                        exc_info=True,
                    )

            # If all candidates failed, fall through to legacy / error handling
            if last_error:
                logger.error(
                    f"Failed to generate presigned URL for document {doc_id} after trying candidates: {candidates}. "
                    f"Last error: {last_error}"
                )

        return Response(
            {
                "success": False,
                "error": "Download URL unavailable for this document",
            },
            status=status.HTTP_404_NOT_FOUND,
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


def _is_safe_lookup_code(value: str, max_len: int = 120) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip()
    if not normalized or len(normalized) > max_len:
        return False
    return bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_\- ]*', normalized))


def _resolve_and_authorize_company_scope(user, company_code: str = '', subfolder_code: str = ''):
    """
    Validate company/subfolder codes and return tenant-authorized objects.
    Raises ValueError for malformed/unresolvable inputs and PermissionError for tenant violations.
    """
    folder = None
    subfolder = None

    if company_code:
        if not _is_safe_lookup_code(company_code):
            raise ValueError("Invalid company code format")
        folder = CompanyFolder.objects.filter(code__iexact=company_code.strip(), is_active=True).first()
        if not folder:
            raise ValueError("Company folder not found")
        if hasattr(folder, 'tenant_id') and getattr(user, 'tenant_id', None):
            if folder.tenant_id and folder.tenant_id != user.tenant_id:
                raise PermissionError("Forbidden")

    if subfolder_code:
        if not folder:
            raise ValueError("Subfolder requires a company folder")
        if not _is_safe_lookup_code(subfolder_code):
            raise ValueError("Invalid subfolder code format")
        subfolder = CompanySubfolder.objects.filter(
            company_folder=folder,
            code__iexact=subfolder_code.strip(),
            is_active=True,
        ).first()
        if not subfolder:
            raise ValueError("Subfolder not found")
        if hasattr(subfolder, 'tenant_id') and getattr(user, 'tenant_id', None):
            if subfolder.tenant_id and subfolder.tenant_id != user.tenant_id:
                raise PermissionError("Forbidden")

    return folder, subfolder


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_company_folders(request):
    """
    List all active company folders for the current tenant (if available).
    """
    try:
        current_user = _get_authenticated_user(request)
        if not current_user:
            return Response({'success': False, 'error': 'Authentication required', 'folders': []}, status=status.HTTP_401_UNAUTHORIZED)
        is_admin = _is_system_admin(current_user)

        queryset = CompanyFolder.objects.filter(is_active=True).order_by('name')

        # If the model has tenant information and a current tenant is set,
        # filter by tenant. We avoid hard dependency on tenant context here.
        if hasattr(CompanyFolder, 'tenant'):
            tenant_id = getattr(current_user, 'tenant_id', None)
            if tenant_id:
                queryset = queryset.filter(tenant__tenant_id=tenant_id)

        folders = []
        # Pre-load any blocking audits so we can expose a simple can_delete flag.
        # A folder is considered blocked if either:
        # - Its code encodes an AuditId whose status is protected, OR
        # - Any linked ai_audit_data rows reference its FileOperations.
        from grc.models import CompanySubfolder, CompanySubfolderDocument
        blocking_folder_ids = set()
        try:
            with create_direct_mysql_client() as conn:
                cur = conn.cursor()
                for folder in queryset:
                    # 1) Block by folder code -> inferred AuditId
                    inferred_status = None
                    if folder.code:
                        parts = str(folder.code).rsplit("_", 1)
                        if len(parts) == 2 and parts[1].isdigit():
                            inferred_audit_id = int(parts[1])
                            cur.execute(
                                "SELECT Status FROM audit WHERE AuditId = %s",
                                [inferred_audit_id],
                            )
                            row = cur.fetchone()
                            inferred_status = row[0] if row else None
                            if inferred_status in ("Work In Progress", "Under review", "Completed"):
                                blocking_folder_ids.add(folder.folder_id)
                                continue

                    # 2) Block by any linked ai_audit_data records
                    subfolders = CompanySubfolder.objects.filter(company_folder=folder)
                    links = CompanySubfolderDocument.objects.filter(company_subfolder__in=subfolders)
                    file_op_ids = [d.file_operation_id for d in links if getattr(d, "file_operation_id", None)]
                    if not file_op_ids:
                        continue
                    format_strings = ",".join(["%s"] * len(file_op_ids))
                    cur.execute(
                        f"""
                        SELECT DISTINCT a.AuditId, a.Status
                        FROM ai_audit_data d
                        JOIN audit a ON d.audit_id = a.AuditId
                        WHERE d.file_operation_id IN ({format_strings})
                        """,
                        file_op_ids,
                    )
                    for audit_id, status_val in cur.fetchall():
                        if status_val in ("Work In Progress", "Under review", "Completed"):
                            blocking_folder_ids.add(folder.folder_id)
                            break
        except Exception:
            blocking_folder_ids = set()
        for folder in queryset:
            # Decrypt name/code/description so UI never shows raw encrypted text
            raw_code = folder.code or ''
            raw_name = folder.name or ''
            raw_desc = folder.description or ''
            code = (decrypt_any_encrypted_value(raw_code) if isinstance(raw_code, str) else raw_code) or raw_code
            name = (decrypt_any_encrypted_value(raw_name) if isinstance(raw_name, str) else raw_name) or raw_name
            description = (decrypt_any_encrypted_value(raw_desc) if isinstance(raw_desc, str) else raw_desc) or raw_desc
            if not isinstance(code, str):
                code = str(code)
            if not isinstance(name, str):
                name = str(name)
            if description is None or not isinstance(description, str):
                description = description if isinstance(description, str) else ''
            # Never send encrypted-looking values to the UI (avoids garbled/overlapping display)
            code = _safe_for_display(code) if code else code
            name = _safe_for_display(name) if name else name
            description = _safe_for_display(description) if description else description
            # Count documents: sum of subfolder counts so folder total matches what user sees in subfolders
            prefix = f"{sanitize_filename_part(raw_code)}_"
            subfolders_of_folder = CompanySubfolder.objects.filter(company_folder=folder)
            linked_ids = list(
                CompanySubfolderDocument.objects.filter(
                    company_subfolder__in=subfolders_of_folder
                ).values_list('file_operation_id', flat=True)
            )
            base_qs = FileOperations.objects.filter(operation_type='upload').exclude(user_id='export_user')
            base_qs = _scope_file_operations_queryset(base_qs, current_user, is_admin=is_admin)
            if linked_ids:
                doc_count = base_qs.filter(
                    Q(file_name__istartswith=prefix) | Q(id__in=linked_ids)
                ).count()
            else:
                doc_count = base_qs.filter(file_name__istartswith=prefix).count()
            # If we have subfolders, use sum of subfolder counts so folder "Files" matches subfolder totals
            if subfolders_of_folder.exists():
                subfolder_total = 0
                for sub in subfolders_of_folder:
                    sub_prefix = f"{prefix}{sanitize_filename_part(sub.code or '')}_"
                    sub_linked = list(
                        CompanySubfolderDocument.objects.filter(company_subfolder=sub).values_list('file_operation_id', flat=True)
                    )
                    if sub_linked:
                        subfolder_total += base_qs.filter(Q(file_name__istartswith=sub_prefix) | Q(id__in=sub_linked)).count()
                    else:
                        subfolder_total += base_qs.filter(file_name__istartswith=sub_prefix).count()
                doc_count = max(doc_count, subfolder_total)
            folders.append({
                'id': folder.folder_id,
                'name': _sanitize_text_output(name, max_len=120),
                'code': _sanitize_text_output(code, max_len=120),
                'description': _sanitize_text_output(description, max_len=400),
                'document_count': doc_count,
                'can_delete': folder.folder_id not in blocking_folder_ids,
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
                'error': CLIENT_SAFE_ERROR,
                'folders': [],
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_company_folder(request):
    """
    Create a new company folder.
    """
    try:
        current_user = _get_authenticated_user(request)
        if not current_user:
            return Response({'success': False, 'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        if not _is_system_admin(current_user):
            return Response({'success': False, 'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        name = _sanitize_folder_name(request.data.get('name') or '')
        description = _sanitize_text_output((request.data.get('description') or '').strip(), max_len=400)

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
        existing = CompanyFolder.objects.filter(code__iexact=code, is_active=True)
        if hasattr(CompanyFolder, 'tenant_id') and getattr(current_user, 'tenant_id', None):
            existing = existing.filter(tenant_id=current_user.tenant_id)
        existing = existing.first()
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
            if current_user:
                folder.created_by = current_user
                folder.updated_by = current_user
                if hasattr(folder, 'tenant_id') and getattr(current_user, 'tenant_id', None):
                    folder.tenant_id = current_user.tenant_id
        except Exception as map_exc:
            logger.warning(f"Could not map request.user to Users: {map_exc}")

        folder.save()

        return Response(
            {
                'success': True,
                'folder': {
                    'id': folder.folder_id,
                    'name': _sanitize_text_output(folder.name, max_len=120),
                    'code': _sanitize_text_output(folder.code, max_len=120),
                    'description': _sanitize_text_output(folder.description or '', max_len=400),
                },
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as exc:
        logger.error(f"Error creating company folder: {exc}", exc_info=True)
        return Response(
            {
                'success': False,
                'error': CLIENT_SAFE_ERROR,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@csrf_exempt
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_company_folder(request, folder_id):
    """
    Delete a company folder and its subfolders/links.
    Files in S3 / file_operations are NOT deleted.
    """
    try:
        current_user = _get_authenticated_user(request)
        if not current_user:
            return Response({'success': False, 'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        if not _is_system_admin(current_user):
            return Response({'success': False, 'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        from grc.models import CompanySubfolderDocument  # Lazy import to avoid heavy imports

        folder = CompanyFolder.objects.filter(folder_id=folder_id, is_active=True).first()
        if not folder:
            return Response(
                {
                    'success': False,
                    'error': 'Company folder not found',
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        if hasattr(folder, 'tenant_id') and getattr(current_user, 'tenant_id', None):
            if folder.tenant_id and folder.tenant_id != current_user.tenant_id:
                return Response(
                    {'success': False, 'error': 'Forbidden'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Before deleting, ensure this folder does not contain evidence needed
        # for audits that are already in progress or completed.
        from grc.models import Audit, CompanySubfolderDocument

        # Folders created for AI audits typically have code that includes the audit id,
        # but to be safe we look for any linked FileOperations and resolve audits
        # that reference their evidence.
        blocking_audits = set()
        # Any subfolder documents in this folder?
        subfolders = CompanySubfolder.objects.filter(company_folder=folder)
        linked_docs = CompanySubfolderDocument.objects.filter(company_subfolder__in=subfolders)
        file_op_ids = [d.file_operation_id for d in linked_docs if getattr(d, "file_operation_id", None)]
        if file_op_ids:
            with create_direct_mysql_client() as conn:
                cur = conn.cursor()
                # ai_audit_data links file_operations via stored_name / document_path in many deployments;
                # here we conservatively check any ai_audit_data rows that reference the same S3 key.
                format_strings = ",".join(["%s"] * len(file_op_ids))
                try:
                    cur.execute(
                        f"""
                        SELECT DISTINCT a.AuditId, a.Status
                        FROM ai_audit_data d
                        JOIN audit a ON d.audit_id = a.AuditId
                        WHERE d.file_operation_id IN ({format_strings})
                        """,
                        file_op_ids,
                    )
                    for audit_id, status_val in cur.fetchall():
                        if status_val in ("Work In Progress", "Under review", "Completed"):
                            blocking_audits.add((audit_id, status_val))
                except Exception:
                    # If this lookup fails, fall back to allowing delete rather than blocking everything.
                    pass

        if blocking_audits:
            return Response(
                {
                    "success": False,
                    "error": "This company folder contains evidence for audits that are in progress or completed "
                             "and cannot be deleted.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Find all subfolders under this company folder
        subfolders = CompanySubfolder.objects.filter(company_folder=folder)

        # Remove all document links in these subfolders
        CompanySubfolderDocument.objects.filter(company_subfolder__in=subfolders).delete()

        # Delete subfolders themselves
        subfolders.delete()

        # Soft-delete the company folder so it no longer appears in lists
        folder.is_active = False
        folder.save(update_fields=['is_active'])

        return Response(
            {
                'success': True,
                'message': 'Company folder deleted successfully',
            },
            status=status.HTTP_200_OK,
        )
    except Exception as exc:
        logger.error(f"Error deleting company folder {folder_id}: {exc}", exc_info=True)
        return Response(
            {
                'success': False,
                'error': CLIENT_SAFE_ERROR,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_company_subfolders(request, folder_id):
    """
    List subfolders for a company folder. Returns id, name, code, document_count.
    """
    try:
        current_user = _get_authenticated_user(request)
        if not current_user:
            return Response({'success': False, 'error': 'Authentication required', 'subfolders': []}, status=status.HTTP_401_UNAUTHORIZED)
        is_admin = _is_system_admin(current_user)

        company_folder = CompanyFolder.objects.filter(
            folder_id=folder_id, is_active=True
        ).first()
        if not company_folder:
            return Response(
                {'success': False, 'error': 'Company folder not found', 'subfolders': []},
                status=status.HTTP_404_NOT_FOUND,
            )
        if hasattr(company_folder, 'tenant_id') and getattr(current_user, 'tenant_id', None):
            if company_folder.tenant_id and company_folder.tenant_id != current_user.tenant_id:
                return Response(
                    {'success': False, 'error': 'Forbidden', 'subfolders': []},
                    status=status.HTTP_403_FORBIDDEN,
                )
        queryset = CompanySubfolder.objects.filter(
            company_folder_id=folder_id, is_active=True
        ).order_by('name')
        company_prefix = f"{sanitize_filename_part(company_folder.code)}_"
        subfolders = []
        for sub in queryset:
            raw_name = sub.name or ''
            raw_code = sub.code or ''
            name = (decrypt_any_encrypted_value(raw_name) if isinstance(raw_name, str) else raw_name) or raw_name
            code = (decrypt_any_encrypted_value(raw_code) if isinstance(raw_code, str) else raw_code) or raw_code
            if not isinstance(name, str):
                name = str(name)
            if not isinstance(code, str):
                code = str(code)
            prefix = f"{company_prefix}{sanitize_filename_part(raw_code)}_"
            # Include docs by file_name prefix OR linked via CompanySubfolderDocument (e.g. AI audit evidence)
            linked_ids = list(
                CompanySubfolderDocument.objects.filter(company_subfolder=sub).values_list('file_operation_id', flat=True)
            )
            base_qs = FileOperations.objects.filter(operation_type='upload').exclude(user_id='export_user')
            base_qs = _scope_file_operations_queryset(base_qs, current_user, is_admin=is_admin)
            if linked_ids:
                doc_count = base_qs.filter(
                    Q(file_name__istartswith=prefix) | Q(id__in=linked_ids)
                ).count()
            else:
                doc_count = base_qs.filter(file_name__istartswith=prefix).count()
            subfolders.append({
                'id': sub.subfolder_id,
                'name': _sanitize_text_output(name, max_len=120),
                'code': _sanitize_text_output(code, max_len=120),
                'document_count': doc_count,
            })
        return Response(
            {'success': True, 'subfolders': subfolders},
            status=status.HTTP_200_OK,
        )
    except Exception as exc:
        logger.error(f"Error listing company subfolders: {exc}", exc_info=True)
        return Response(
            {'success': False, 'error': CLIENT_SAFE_ERROR, 'subfolders': []},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_company_subfolder(request, folder_id):
    """
    Create a subfolder inside a company folder.
    """
    try:
        current_user = _get_authenticated_user(request)
        if not current_user:
            return Response({'success': False, 'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        if not _is_system_admin(current_user):
            return Response({'success': False, 'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        company_folder = CompanyFolder.objects.filter(
            folder_id=folder_id, is_active=True
        ).first()
        if not company_folder:
            return Response(
                {'success': False, 'error': 'Company folder not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if hasattr(company_folder, 'tenant_id') and getattr(current_user, 'tenant_id', None):
            if company_folder.tenant_id and company_folder.tenant_id != current_user.tenant_id:
                return Response(
                    {'success': False, 'error': 'Forbidden'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        name = _sanitize_folder_name(request.data.get('name') or '')
        if not name:
            return Response(
                {'success': False, 'error': 'Name is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        code = sanitize_filename_part(name)
        existing = CompanySubfolder.objects.filter(
            company_folder_id=folder_id, code__iexact=code, is_active=True
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
                    'name': _sanitize_text_output(subfolder.name, max_len=120),
                    'code': _sanitize_text_output(subfolder.code, max_len=120),
                },
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as exc:
        logger.error(f"Error creating company subfolder: {exc}", exc_info=True)
        return Response(
            {'success': False, 'error': CLIENT_SAFE_ERROR},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def upload_document(request):
    """
    Upload document with optional framework selection
    Naming convention: framework_module_datetime.filetype (if framework selected)
    Or: module_datetime.filetype (if no framework)
    """
    current_user = _get_authenticated_user(request)
    if not current_user:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    is_admin = _is_system_admin(current_user)
    try:
        # Get form data
        uploaded_file = request.FILES.get('file')
        module = (request.data.get('module') or '').strip().lower()
        framework = (request.data.get('framework', '') or '').strip()
        # Optional company code and subfolder (from company folders dropdown)
        company_code = (request.data.get('company', '') or request.data.get('company_code', '') or '').strip()
        subfolder_code = (request.data.get('subfolder', '') or request.data.get('subfolder_code', '') or '').strip()
        user_id = str(current_user.UserId)
        
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
        if module not in ALLOWED_UPLOAD_MODULES:
            return Response({
                'success': False,
                'error': 'Invalid module'
            }, status=status.HTTP_400_BAD_REQUEST)
        if framework and len(framework) > 120:
            return Response({
                'success': False,
                'error': 'Invalid framework'
            }, status=status.HTTP_400_BAD_REQUEST)
        if company_code and not _is_safe_lookup_code(company_code):
            return Response({
                'success': False,
                'error': 'Invalid company'
            }, status=status.HTTP_400_BAD_REQUEST)
        if subfolder_code and not _is_safe_lookup_code(subfolder_code):
            return Response({
                'success': False,
                'error': 'Invalid subfolder'
            }, status=status.HTTP_400_BAD_REQUEST)

        resolved_folder = None
        resolved_subfolder = None
        if company_code or subfolder_code:
            try:
                resolved_folder, resolved_subfolder = _resolve_and_authorize_company_scope(
                    current_user, company_code=company_code, subfolder_code=subfolder_code
                )
            except PermissionError:
                logger.info(
                    "Document uploaded: operation_id=%s actor_user_id=%s module=%s",
                    operation_id,
                    getattr(current_user, 'UserId', None),
                    module,
                )
                return Response({
                    'success': False,
                    'error': 'Forbidden'
                }, status=status.HTTP_403_FORBIDDEN)
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Invalid company/subfolder'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Security: validate file type, MIME, magic bytes, and content
        from grc.utils.file_validation import validate_upload
        validation = validate_upload(uploaded_file, max_size_mb=25)
        if not validation.is_valid:
            logger.warning(
                "Blocked malicious/invalid upload: user=%s file=%s reason=%s",
                user_id, uploaded_file.name, validation.error,
            )
            return Response({
                'success': False,
                'error': validation.error
            }, status=status.HTTP_400_BAD_REQUEST)
        # Convert framework name/id to framework_id if framework is provided
        framework_id = None
        if framework:
            try:
                from ...models import Framework
                framework_obj = None
                framework_str = str(framework).strip()
                if framework_str.isdigit():
                    framework_obj = Framework.objects.filter(FrameworkId=int(framework_str)).first()
                if framework_obj is None:
                    framework_obj = Framework.objects.filter(FrameworkName=framework_str).first()
                if framework_obj:
                    framework_id = framework_obj.FrameworkId
                    if not is_admin and int(getattr(current_user, 'FrameworkId_id', 0) or 0) != int(framework_id):
                        return Response({
                            'success': False,
                            'error': 'Forbidden framework selection'
                        }, status=status.HTTP_403_FORBIDDEN)
                else:
                    return Response({
                        'success': False,
                        'error': 'Invalid framework'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.warning(f"⚠️ Error looking up framework '{framework}': {str(e)}")
                return Response({
                    'success': False,
                    'error': 'Invalid framework'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            framework_id = getattr(current_user, 'FrameworkId_id', None)
 
        # Get file extension from a safe filename component only
        original_filename = safe_upload_filename(uploaded_file.name)
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
            approved_temp_dir = _get_approved_temp_upload_dir()
            # Create temporary file inside approved app directory only.
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension, dir=approved_temp_dir) as temp_file:
                # Write uploaded file content to temp file
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            if not resolved_path_under_base(temp_file_path, approved_temp_dir):
                raise UnsafePathError("Temporary upload path escaped approved directory")
            
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
                        if not _can_access_file_operation(file_op, current_user, is_admin=is_admin):
                            return Response({
                                'success': False,
                                'error': 'Forbidden'
                            }, status=status.HTTP_403_FORBIDDEN)
                        file_op.file_name = custom_filename
                        file_op.original_name = custom_filename
                        file_op.user_id = user_id
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
                        update_fields = ['file_name', 'original_name', 'user_id']
                        if expiry_date:
                            file_op.retentionExpiry = expiry_date
                            update_fields.append('retentionExpiry')
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

                # Create link to company subfolder if applicable
                if operation_id and resolved_subfolder:
                    try:
                        CompanySubfolderDocument.objects.get_or_create(
                            company_subfolder=resolved_subfolder,
                            file_operation_id=operation_id,
                            defaults={
                                'document_link': upload_result.get('file_info', {}).get('url', ''),
                                's3_key': upload_result.get('file_info', {}).get('s3Key', '')
                            }
                        )
                        logger.info(f"✅ Linked file {operation_id} to subfolder {resolved_subfolder.subfolder_id}")
                    except Exception as link_err:
                        logger.warning(f"⚠️ Failed to link file {operation_id} to subfolder: {link_err}")
                
                return Response({
                    'success': True,
                    'message': 'Document uploaded successfully',
                    'stored_name': upload_result.get('file_info', {}).get('storedName'),
                    'original_name': custom_filename,
                    'custom_name': custom_filename,
                    # s3_url intentionally omitted — use /api/documents/<id>/download-url/ for a signed URL
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
                    'error': 'Upload failed'
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
            'error': CLIENT_SAFE_ERROR
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)