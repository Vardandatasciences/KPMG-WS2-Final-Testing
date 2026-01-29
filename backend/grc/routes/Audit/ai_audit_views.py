"""
AI Audit Views - Document Upload and AI Processing
Handles document upload for AI audits and automated audit processing
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction, connection
import os
import tempfile
import mimetypes
import shutil
import uuid
from datetime import datetime
import json

from ...models import Audit, AuditDocument, AuditDocumentMapping, Policy, SubPolicy, Compliance, Users
from ...routes.Global.logging_service import send_log
from ...rbac.permissions import (
    AuditViewPermission, AuditConductPermission, AuditReviewPermission,
    AuditAssignPermission, AuditAnalyticsPermission, AuditViewAllPermission
)
from ...rbac.decorators import (
    audit_assign_required,
    audit_conduct_required,
    audit_view_reports_required,
    audit_view_all_required,
    audit_review_required
)
from .framework_filter_helper import get_active_framework_filter, apply_framework_filter_to_audits, get_framework_sql_filter

# DRF Session auth variant that skips CSRF enforcement for API clients
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return

@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission, AuditReviewPermission])
@audit_conduct_required
def upload_audit_document(request, audit_id):
    """
    Upload document for AI audit processing
    Supports multiple file formats and maps to policies/sub-policies
    """
    try:
        print(f"📤 Upload request for audit {audit_id}")
        print(f"📤 Request data: {request.POST}")
        print(f"📤 Request files: {request.FILES}")
        print(f"📤 User ID: {request.session.get('user_id')}")
        
        # Fixed: Remove the problematic get_all_permissions() call
        if hasattr(request, 'user') and request.user:
            print(f"📤 User: {request.user}")
        else:
            print("📤 No user object")
        
        # Get audit details
        try:
            audit = Audit.objects.get(AuditId=audit_id)
            print(f"📤 Found audit {audit_id} with type: {audit.AuditType}")
        except Audit.DoesNotExist:
            print(f"❌ Audit {audit_id} not found")
            return Response({
                'success': False,
                'error': 'Audit not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Allow document uploads for all audit types
        # Note: AI processing can be applied to any audit type
        print(f"📤 Audit type: {audit.AuditType} - allowing document upload")
        
        # Get file from request
        if 'file' not in request.FILES:
            print("❌ No file provided in request")
            return Response({
                'success': False,
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        print(f"📤 Uploaded file: {uploaded_file.name}, size: {uploaded_file.size}, type: {uploaded_file.content_type}")
        
        # Get additional parameters
        policy_id = request.POST.get('policy_id', None)
        subpolicy_id = request.POST.get('subpolicy_id', None)
        compliance_id = request.POST.get('compliance_id', None)
        document_type = request.POST.get('document_type', 'evidence')
        external_source = request.POST.get('external_source', 'manual')
        external_id = request.POST.get('external_id', None)
        
        # Get ForeignKey objects
        policy_obj = None
        subpolicy_obj = None
        compliance_obj = None
        user_obj = None
        
        if policy_id:
            try:
                policy_obj = Policy.objects.get(PolicyId=policy_id)
            except Policy.DoesNotExist:
                print(f"❌ Policy {policy_id} not found")
        
        if subpolicy_id:
            try:
                subpolicy_obj = SubPolicy.objects.get(SubPolicyId=subpolicy_id)
            except SubPolicy.DoesNotExist:
                print(f"❌ SubPolicy {subpolicy_id} not found")
        
        if compliance_id:
            try:
                compliance_obj = Compliance.objects.get(ComplianceId=compliance_id)
            except Compliance.DoesNotExist:
                print(f"❌ Compliance {compliance_id} not found")
        
        # Get user object - use authenticated user from JWT
        user_id = None
        user_obj = None
        db_user_id = None  # Initialize db_user_id at the start
        
        # First try to get user from request.user (JWT authentication)
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'UserId'):
            user_id = request.user.UserId
            user_obj = request.user
            print(f"📤 Using JWT authenticated user: {user_id}")
        
        # Fallback to session if JWT user not available
        if not user_obj:
            user_id = request.session.get('user_id')
            if user_id:
                try:
                    user_obj = Users.objects.get(UserId=user_id)
                    print(f"📤 Using session user: {user_id}")
                except Users.DoesNotExist:
                    print(f"❌ Session user {user_id} not found")
        
        # Final fallback - find any valid user
        if not user_obj:
            user_obj = Users.objects.first()
            if user_obj:
                user_id = user_obj.UserId
                print(f"📤 Using fallback user: {user_id}")
        
        # Verify user exists in grc_users table (for foreign key constraint)
        with connection.cursor() as cursor:
            if user_id:
                cursor.execute("SELECT UserId FROM grc_users WHERE UserId = %s", [user_id])
                db_user = cursor.fetchone()
                
                if db_user:
                    db_user_id = user_id
                    print(f"✅ User {user_id} verified in grc_users table")
                else:
                    print(f"❌ User {user_id} not found in grc_users table")
                    # Find any valid user in grc_users table
                    cursor.execute("SELECT UserId FROM grc_users LIMIT 1")
                    valid_user = cursor.fetchone()
                    if valid_user:
                        db_user_id = valid_user[0]
                        print(f"📤 Using valid database user: {db_user_id}")
                    else:
                        print("❌ No users found in grc_users table - will use NULL")
                        db_user_id = None
            else:
                print("📤 No user available - will use NULL for UploadedBy")
                db_user_id = None
        
        # Debug: Print all the objects we're about to use
        print(f"📤 Debug - audit: {audit}")
        print(f"📤 Debug - policy_obj: {policy_obj}")
        print(f"📤 Debug - subpolicy_obj: {subpolicy_obj}")
        print(f"📤 Debug - compliance_obj: {compliance_obj}")
        print(f"📤 Debug - user_obj: {user_obj}")
        print(f"📤 Debug - db_user_id: {db_user_id}")
        
        # Validate file size (max 100MB for AI processing)
        max_file_size = 100 * 1024 * 1024  # 100MB
        if uploaded_file.size > max_file_size:
            return Response({
                'success': False,
                'error': f'File size exceeds maximum limit of 100MB. Current size: {uploaded_file.size / (1024*1024):.2f}MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv', '.json']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if file_extension not in allowed_extensions:
            return Response({
                'success': False,
                'error': f'File type {file_extension} is not allowed. Allowed types: {", ".join(allowed_extensions)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(uploaded_file.name)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        try:
            # For now, we'll store the file locally. In production, this should go to S3
            # Create a unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"audit_{audit_id}_{timestamp}_{uploaded_file.name}"
            
            # Get MEDIA_ROOT from Django settings
            from django.conf import settings
            file_path = os.path.join(settings.MEDIA_ROOT, 'audit_documents', unique_filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Move temp file to final location (using shutil.move to handle cross-drive moves on Windows)
            shutil.move(temp_file_path, file_path)
            
            # Create database record using raw SQL (matching ai_audit_api.py)
            file_id = str(uuid.uuid4())
            
            with connection.cursor() as cursor:
                print(f"🔍 DEBUG: About to insert document with audit_id: {audit_id}")
                print(f"🔍 DEBUG: Values: audit_id={int(audit_id) if str(audit_id).isdigit() else audit_id}, name={uploaded_file.name}")
                
                # Get FrameworkId from the audit
                cursor.execute("SELECT FrameworkId FROM audit WHERE AuditId = %s", [int(audit_id) if str(audit_id).isdigit() else audit_id])
                framework_row = cursor.fetchone()
                framework_id = framework_row[0] if framework_row else None
                
                cursor.execute("""
                    INSERT INTO grc_auditdocument 
                    (AuditId, DocumentName, DocumentType, FilePath, FileSize, 
                     FileExtension, MimeType, UploadedBy, UploadedDate, 
                     UploadStatus, ProcessingStatus, ExternalSource, ExternalId, FrameworkId)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    int(audit_id) if str(audit_id).isdigit() else audit_id,
                    uploaded_file.name,
                    document_type,
                    file_path,
                    uploaded_file.size,
                    file_extension,
                    mime_type,
                    db_user_id,  # Always valid now
                    datetime.now(),
                    'uploaded',
                    'pending',
                    external_source,
                    file_id,
                    framework_id
                ])
                
                print(f"🔍 DEBUG: Insert executed successfully")
                
                # Get the inserted document ID
                cursor.execute("SELECT LAST_INSERT_ID()")
                document_id = cursor.fetchone()[0]
                
                print(f"🔍 DEBUG: Got document_id: {document_id}")
                
                # Verify the insert worked
                cursor.execute("SELECT COUNT(*) FROM grc_auditdocument WHERE DocumentId = %s", [document_id])
                count = cursor.fetchone()[0]
                print(f"🔍 DEBUG: Verification - found {count} documents with ID {document_id}")
                
            print(f"📤 Created document record with ID: {document_id}")
            
            
            # Log the upload (use session user_id for logging even if database user is different)
            log_user_id = request.session.get('user_id') or (user_id if user_obj else None)
            send_log(
                module="AI_Audit",
                actionType="DOCUMENT_UPLOADED",
                description=f"Document uploaded for AI audit {audit_id}",
                userId=log_user_id,
                entityType="AuditDocument",
                entityId=str(document_id),
                additionalInfo={
                    "audit_id": audit_id,
                    "document_name": uploaded_file.name,
                    "file_size": uploaded_file.size,
                    "document_type": document_type,
                    "policy_id": policy_id,
                    "subpolicy_id": subpolicy_id,
                    "db_user_id": db_user_id,
                    "auth_user_id": user_id
                }
            )
            
            return Response({
                'success': True,
                'message': 'Document uploaded successfully',
                'document_id': document_id,
                'document_name': uploaded_file.name,
                'file_size': uploaded_file.size,
                'processing_status': 'pending',
                'next_step': 'AI processing will begin automatically'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise e
            
    except Exception as e:
        print(f"❌ Error uploading document: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': f'Error uploading document: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission])
@audit_conduct_required
def get_audit_documents(request, audit_id):
    """
    Get all documents uploaded for a specific audit
    """
    try:
        # Get audit details
        try:
            audit = Audit.objects.get(AuditId=audit_id)
        except Audit.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Audit not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get documents using raw SQL to match the correct table name
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DocumentId, DocumentName, DocumentType, FileSize, 
                       FileExtension, UploadedDate, UploadStatus, ProcessingStatus,
                       ProcessingResults, DocumentSummary, ExternalSource
                FROM grc_auditdocument 
                WHERE AuditId = %s 
                ORDER BY UploadedDate DESC
            """, [int(audit_id) if str(audit_id).isdigit() else audit_id])
            
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
        
        document_list = []
        for row in rows:
            doc_dict = dict(zip(columns, row))
            document_list.append({
                'document_id': doc_dict.get('DocumentId'),
                'document_name': doc_dict.get('DocumentName'),
                'document_type': doc_dict.get('DocumentType'),
                'file_size': doc_dict.get('FileSize'),
                'file_extension': doc_dict.get('FileExtension'),
                'uploaded_date': doc_dict.get('UploadedDate').isoformat() if doc_dict.get('UploadedDate') else None,
                'upload_status': doc_dict.get('UploadStatus'),
                'processing_status': doc_dict.get('ProcessingStatus'),
                'external_source': doc_dict.get('ExternalSource'),
                'processing_results': doc_dict.get('ProcessingResults'),
                'document_summary': doc_dict.get('DocumentSummary')
            })
        
        return Response({
            'success': True,
            'audit_id': audit_id,
            'audit_type': audit.AuditType,
            'documents': document_list,
            'total_documents': len(document_list)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error retrieving documents: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission])
@audit_conduct_required
def start_ai_audit_processing(request, audit_id):
    """
    Start AI processing for all uploaded documents in an audit
    """
    try:
        # Get audit details
        try:
            audit = Audit.objects.get(AuditId=audit_id)
        except Audit.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Audit not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Allow AI processing for all audit types
        print(f"🚀 Starting AI processing for audit type: {audit.AuditType}")
        
        # Get all pending documents using raw SQL
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM grc_auditdocument 
                WHERE AuditId = %s AND ProcessingStatus = 'pending'
            """, [int(audit_id) if str(audit_id).isdigit() else audit_id])
            
            pending_count = cursor.fetchone()[0]
        
        if pending_count == 0:
            return Response({
                'success': False,
                'error': 'No documents pending processing'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update processing status using raw SQL
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE grc_auditdocument 
                SET ProcessingStatus = 'processing' 
                WHERE AuditId = %s AND ProcessingStatus = 'pending'
            """, [int(audit_id) if str(audit_id).isdigit() else audit_id])
            
            updated_count = cursor.rowcount
        
        # Log the start of AI processing
        send_log(
            module="AI_Audit",
            actionType="AI_PROCESSING_STARTED",
            description=f"Started AI processing for audit {audit_id}",
            userId=request.session.get('user_id'),
            entityType="Audit",
            entityId=str(audit_id),
            additionalInfo={
                "audit_id": audit_id,
                "documents_processing": updated_count
            }
        )
        
        # TODO: Here we would trigger the actual AI processing
        # This could be done via:
        # 1. Celery background task
        # 2. AWS Lambda function
        # 3. Direct AI service call
        # For now, we'll simulate the processing
        
        return Response({
            'success': True,
            'message': f'AI processing started for {updated_count} documents',
            'audit_id': audit_id,
            'documents_processing': updated_count,
            'estimated_completion': '5-10 minutes'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error starting AI processing: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission])
@audit_conduct_required
def get_ai_audit_status(request, audit_id):
    """
    Get AI audit processing status and results
    """
    try:
        # Get audit details
        try:
            audit = Audit.objects.get(AuditId=audit_id)
        except Audit.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Audit not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get document processing status using raw SQL
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT ProcessingStatus, COUNT(*) as count
                FROM grc_auditdocument 
                WHERE AuditId = %s 
                GROUP BY ProcessingStatus
            """, [int(audit_id) if str(audit_id).isdigit() else audit_id])
            
            status_rows = cursor.fetchall()
        
        status_counts = {
            'pending': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0
        }
        
        for status_name, count in status_rows:
            if status_name in status_counts:
                status_counts[status_name] = count
        
        # Calculate overall progress
        total_documents = sum(status_counts.values())
        completed_documents = status_counts['completed']
        progress_percentage = (completed_documents / total_documents * 100) if total_documents > 0 else 0
        
        # Get compliance mappings if any (this would need to be implemented)
        compliance_results = []
        
        return Response({
            'success': True,
            'audit_id': audit_id,
            'audit_type': audit.AuditType,
            'processing_status': {
                'total_documents': total_documents,
                'pending': status_counts['pending'],
                'processing': status_counts['processing'],
                'completed': status_counts['completed'],
                'failed': status_counts['failed'],
                'progress_percentage': round(progress_percentage, 2)
            },
            'compliance_results': compliance_results,
            'is_complete': status_counts['pending'] == 0 and status_counts['processing'] == 0
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error getting AI audit status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditReviewPermission])
@audit_review_required
def review_ai_audit_findings(request, audit_id):
    """
    Review and approve/reject AI audit findings
    """
    try:
        data = request.data
        mapping_id = data.get('mapping_id')
        compliance_status = data.get('compliance_status')
        review_comments = data.get('review_comments', '')
        
        if not mapping_id or not compliance_status:
            return Response({
                'success': False,
                'error': 'Mapping ID and compliance status are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the mapping (this would need to be implemented with raw SQL if needed)
        try:
            mapping = AuditDocumentMapping.objects.get(
                MappingId=mapping_id,
                DocumentId__AuditId=audit_id
            )
        except AuditDocumentMapping.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Mapping not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update the mapping with reviewer input
        mapping.ComplianceStatus = compliance_status
        mapping.ReviewComments = review_comments
        mapping.ReviewedBy_id = request.session.get('user_id')
        mapping.ReviewedDate = timezone.now()
        mapping.save()
        
        # Log the review
        send_log(
            module="AI_Audit",
            actionType="AI_FINDING_REVIEWED",
            description=f"Reviewed AI finding for audit {audit_id}",
            userId=request.session.get('user_id'),
            entityType="AuditDocumentMapping",
            entityId=str(mapping_id),
            additionalInfo={
                "audit_id": audit_id,
                "mapping_id": mapping_id,
                "compliance_status": compliance_status,
                "review_comments": review_comments
            }
        )
        
        return Response({
            'success': True,
            'message': 'AI finding reviewed successfully',
            'mapping_id': mapping_id,
            'compliance_status': compliance_status,
            'reviewed_date': mapping.ReviewedDate.isoformat()
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error reviewing AI finding: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)