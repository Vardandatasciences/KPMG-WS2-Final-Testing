"""
Access Request Views for TPRM System

Handles creation, retrieval, and approval/rejection of access requests
"""

import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import connection, connections
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .tprm_utils import RBACTPRMUtils
from .models import RBACTPRM, AccessRequestTPRM

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def create_access_request(request):
    """
    Create a new access request for TPRM
    """
    try:
        # Log incoming request for debugging
        logger.info(f"[TPRM Access Request] Received request - Method: {request.method}, Content-Type: {request.content_type}")
        logger.info(f"[TPRM Access Request] Authorization header: {request.headers.get('Authorization', 'Not present')[:50] if request.headers.get('Authorization') else 'Not present'}")
        
        # Get request data first (this consumes the body stream)
        request_data = request.data
        logger.info(f"[TPRM Access Request] Request data: {request_data}")
        
        # Get user ID from request
        user_id = RBACTPRMUtils.get_user_id_from_request(request)
        
        # Fallback: Try to get user_id from request data if not found in token/session
        if not user_id:
            user_id = request_data.get('user_id')
            if user_id:
                try:
                    user_id = int(user_id)
                    logger.info(f"[TPRM Access Request] Got user_id from request data: {user_id}")
                except (ValueError, TypeError):
                    logger.warning(f"[TPRM Access Request] Invalid user_id in request data: {user_id}")
                    user_id = None
        
        logger.info(f"[TPRM Access Request] Final extracted user_id: {user_id}")
        
        if not user_id:
            logger.warning(f"[TPRM Access Request] User not authenticated - no user_id found in token, session, or request data")
            return Response(
                {'status': 'error', 'message': 'User not authenticated. Please log in and try again.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get request data (already extracted above)
        requested_url = request_data.get('requested_url', '')
        requested_feature = request_data.get('requested_feature', '')
        required_permission = request_data.get('required_permission', '')
        requested_role = request_data.get('requested_role', '')
        message = request_data.get('message', '')
        
        # Log the received data for debugging
        logger.info(f"[TPRM Access Request] Creating access request - User: {user_id}, URL: {requested_url}, Feature: {requested_feature}, Permission: {required_permission}, Role: {requested_role}")
        
        # Create audit trail
        audit_trail = {
            'requested_url': requested_url,
            'requested_feature': requested_feature,
            'required_permission': required_permission,
            'requested_role': requested_role,
            'message': message,
            'requested_by': user_id
        }
        
        # Create the access request using raw SQL (since TPRM uses different database)
        # Use TPRM database connection
        tprm_connection = connections['tprm'] if 'tprm' in connections.databases else connection
        logger.info(f"[TPRM Access Request] Using database connection: {'tprm' if 'tprm' in connections.databases else 'default'}")
        logger.info(f"[TPRM Access Request] Database name: {tprm_connection.settings_dict.get('NAME', 'unknown')}")
        
        try:
            with tprm_connection.cursor() as cursor:
                # First check if table exists
                try:
                    cursor.execute("""
                        SELECT COUNT(*) as table_exists
                        FROM information_schema.tables 
                        WHERE table_schema = DATABASE() 
                        AND table_name = 'AccessRequestTPRM'
                    """)
                    table_check = cursor.fetchone()
                    if not table_check or table_check[0] == 0:
                        logger.error(f"[TPRM Access Request] Table AccessRequestTPRM does not exist in database. Please run the SQL script to create it.")
                        return Response(
                            {'status': 'error', 'message': 'Access request table does not exist. Please contact administrator.'}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                    logger.info(f"[TPRM Access Request] Table AccessRequestTPRM exists in database")
                except Exception as table_check_error:
                    logger.warning(f"[TPRM Access Request] Could not check if table exists: {str(table_check_error)}. Proceeding with insert...")
                
                # Insert the access request
                cursor.execute("""
                    INSERT INTO `AccessRequestTPRM` 
                    (user_id, requested_url, requested_feature, required_permission, requested_role, status, message, audit_trail, approved_by, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    user_id,
                    requested_url or None,
                    requested_feature or None,
                    required_permission or None,
                    requested_role or None,
                    'REQUESTED',
                    message or None,
                    json.dumps(audit_trail),
                    None,  # approved_by is NULL initially
                    timezone.now(),
                    timezone.now()
                ])
                
                request_id = cursor.lastrowid
                logger.info(f"[TPRM Access Request] Access request {request_id} created by user {user_id} - URL: {requested_url}, Permission: {required_permission}")
                
                return Response({
                    'status': 'success',
                    'message': 'Access request created successfully',
                    'data': {
                        'id': request_id,
                        'status': 'REQUESTED',
                        'created_at': timezone.now().isoformat()
                    }
                }, status=status.HTTP_201_CREATED)
                
        except Exception as db_error:
            logger.error(f"[TPRM Access Request] Database error: {str(db_error)}")
            import traceback
            logger.error(f"[TPRM Access Request] Traceback: {traceback.format_exc()}")
            return Response(
                {'status': 'error', 'message': f'Database error: {str(db_error)}. Please ensure the AccessRequestTPRM table exists.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Exception as e:
        logger.error(f"[TPRM Access Request] Error creating access request: {str(e)}")
        import traceback
        logger.error(f"[TPRM Access Request] Full traceback: {traceback.format_exc()}")
        logger.error(f"[TPRM Access Request] Request method: {request.method}")
        logger.error(f"[TPRM Access Request] Request path: {request.path if hasattr(request, 'path') else 'N/A'}")
        return Response(
            {'status': 'error', 'message': f'Failed to create request: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_access_requests(request, user_id):
    """
    Get access requests for a user.
    Admins see all requests, regular users see only their own.
    """
    try:
        logger.info(f"[TPRM Access Request] Getting access requests for user_id: {user_id}")
        
        # Get user making the request
        requesting_user_id = RBACTPRMUtils.get_user_id_from_request(request)
        
        # If not found from JWT/session, use the user_id from URL path as fallback
        if not requesting_user_id:
            try:
                requesting_user_id = int(user_id)
                logger.info(f"[TPRM Access Request] Using user_id from URL path: {requesting_user_id}")
            except (ValueError, TypeError):
                logger.warning(f"[TPRM Access Request] Invalid user_id in URL path: {user_id}")
        
        logger.info(f"[TPRM Access Request] Requesting user_id: {requesting_user_id}")
        
        if not requesting_user_id:
            return Response(
                {'status': 'error', 'message': 'User not authenticated'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is an admin (user IDs 1, 2, 3, or 4, or has admin role)
        admin_user_ids = [1, 2, 3, 4]
        try:
            requesting_user_id_int = int(requesting_user_id)
            is_admin = requesting_user_id_int in admin_user_ids
            
            # Also check if user has admin role in RBAC
            if not is_admin:
                rbac_record = RBACTPRMUtils.get_user_rbac_record(requesting_user_id_int)
                if rbac_record and rbac_record.has_admin_access:
                    is_admin = True
        except (ValueError, TypeError):
            is_admin = False
        
        # Query access requests - use TPRM database connection
        tprm_connection = connections['tprm'] if 'tprm' in connections.databases else connection
        with tprm_connection.cursor() as cursor:
            if is_admin:
                # Admin sees all requests
                cursor.execute("""
                    SELECT 
                        ar.id,
                        ar.user_id,
                        ar.requested_url,
                        ar.requested_feature,
                        ar.required_permission,
                        ar.requested_role,
                        ar.status,
                        ar.created_at,
                        ar.updated_at,
                        ar.approved_by,
                        ar.message,
                        ar.audit_trail,
                        u.FirstName,
                        u.LastName,
                        u.UserName,
                        approver.FirstName as ApproverFirstName,
                        approver.LastName as ApproverLastName
                    FROM `AccessRequestTPRM` ar
                    LEFT JOIN `users` u ON ar.user_id = u.UserId
                    LEFT JOIN `users` approver ON ar.approved_by = approver.UserId
                    ORDER BY ar.created_at DESC
                """)
            else:
                # Regular user sees only their own requests
                cursor.execute("""
                    SELECT 
                        ar.id,
                        ar.user_id,
                        ar.requested_url,
                        ar.requested_feature,
                        ar.required_permission,
                        ar.requested_role,
                        ar.status,
                        ar.created_at,
                        ar.updated_at,
                        ar.approved_by,
                        ar.message,
                        ar.audit_trail,
                        approver.FirstName as ApproverFirstName,
                        approver.LastName as ApproverLastName
                    FROM `AccessRequestTPRM` ar
                    LEFT JOIN `users` approver ON ar.approved_by = approver.UserId
                    WHERE ar.user_id = %s
                    ORDER BY ar.created_at DESC
                """, [int(user_id)])
            
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            
            logger.info(f"[TPRM Access Request] Found {len(rows)} access requests")
            
            requests = []
            for row in rows:
                request_data = dict(zip(columns, row))
                # Parse JSON fields
                if request_data.get('audit_trail'):
                    if isinstance(request_data['audit_trail'], str):
                        try:
                            request_data['audit_trail'] = json.loads(request_data['audit_trail'])
                        except:
                            request_data['audit_trail'] = {}
                
                # Format dates
                if request_data.get('created_at'):
                    request_data['created_at'] = request_data['created_at'].isoformat() if hasattr(request_data['created_at'], 'isoformat') else str(request_data['created_at'])
                if request_data.get('updated_at'):
                    request_data['updated_at'] = request_data['updated_at'].isoformat() if hasattr(request_data['updated_at'], 'isoformat') else str(request_data['updated_at'])
                
                requests.append(request_data)
            
            logger.info(f"[TPRM Access Request] Returning {len(requests)} formatted requests")
            
            return Response({
                'status': 'success',
                'data': requests
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"[TPRM Access Request] Error fetching access requests: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'status': 'error', 'message': f'Failed to fetch access requests: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['PUT'])
@authentication_classes([])
@permission_classes([AllowAny])
def update_access_request_status(request, request_id):
    """
    Update the status of an access request (Approve/Reject)
    Only Administrators can approve/reject requests
    When approved, updates rbac_tprm table with requested permission
    """
    try:
        # Get the request - use TPRM database connection
        tprm_connection = connections['tprm'] if 'tprm' in connections.databases else connection
        with tprm_connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, status, requested_role, required_permission, requested_url, requested_feature, audit_trail
                FROM `AccessRequestTPRM`
                WHERE id = %s
            """, [request_id])
            
            row = cursor.fetchone()
            if not row:
                return Response(
                    {'status': 'error', 'message': 'Request not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            request_data = dict(zip([col[0] for col in cursor.description], row))
            current_status = request_data['status']
            request_user_id = request_data['user_id']
            requested_role = request_data.get('requested_role')
            required_permission = request_data.get('required_permission')
            requested_url = request_data.get('requested_url', '')
            requested_feature = request_data.get('requested_feature', '')
            
            # Get the user making the update from request
            user_id = RBACTPRMUtils.get_user_id_from_request(request)
            if not user_id:
                user_id = request.data.get('user_id')
                if not user_id:
                    return Response(
                        {'status': 'error', 'message': 'User not authenticated'}, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            
            # Check if user is an admin
            admin_user_ids = [1, 2, 3, 4]
            try:
                user_id_int = int(user_id)
                is_admin = user_id_int in admin_user_ids
                
                # Also check if user has admin role in RBAC
                if not is_admin:
                    rbac_record = RBACTPRMUtils.get_user_rbac_record(user_id_int)
                    if rbac_record and rbac_record.has_admin_access:
                        is_admin = True
            except (ValueError, TypeError):
                is_admin = False
            
            if not is_admin:
                return Response(
                    {'status': 'error', 'message': 'Only administrators can approve/reject requests'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get new status from request
            new_status = request.data.get('status')
            if not new_status:
                return Response(
                    {'status': 'error', 'message': 'Status is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate status
            valid_statuses = ['REQUESTED', 'APPROVED', 'REJECTED']
            new_status_upper = new_status.upper()
            if new_status_upper not in valid_statuses:
                return Response(
                    {'status': 'error', 'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if request is already approved or rejected
            if current_status in ['APPROVED', 'REJECTED']:
                return Response(
                    {'status': 'error', 'message': f'Request is already {current_status.lower()}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get audit trail
            audit_trail = {}
            if request_data.get('audit_trail'):
                if isinstance(request_data['audit_trail'], str):
                    try:
                        audit_trail = json.loads(request_data['audit_trail'])
                    except:
                        audit_trail = {}
                elif isinstance(request_data['audit_trail'], dict):
                    audit_trail = request_data['audit_trail']
            
            # Update the request status
            updated_at = timezone.now()
            
            # Add status change to audit trail
            if 'status_changes' not in audit_trail:
                audit_trail['status_changes'] = []
            
            audit_trail['status_changes'].append({
                'from_status': current_status,
                'to_status': new_status_upper,
                'changed_by': user_id,
                'changed_at': updated_at.isoformat()
            })
            
            # If approved, update rbac_tprm table
            if new_status_upper == 'APPROVED':
                try:
                    logger.info(f"[TPRM Access Request] Processing RBAC update for approved access request {request_id}, user {request_user_id}, permission: {required_permission}")
                    
                    # Get or create RBAC entry
                    # Use raw SQL to get fresh data, bypassing ORM cache
                    cursor.execute("""
                        SELECT RBACId, UserId, UserName, Role, IsActive
                        FROM `rbac_tprm`
                        WHERE UserId = %s AND IsActive = 'Y'
                        LIMIT 1
                    """, [request_user_id])
                    rbac_row = cursor.fetchone()
                    
                    if not rbac_row:
                        # No RBAC entry exists, need to create one
                        rbac_entry = None
                    else:
                        # Entry exists, we'll use it for role updates if needed
                        rbac_entry = RBACTPRM.objects.filter(user_id=request_user_id, is_active='Y').first()
                    
                    if not rbac_entry:
                        # Create new RBAC entry
                        # Get user info from users table - use TPRM database
                        cursor.execute("SELECT UserName FROM `users` WHERE UserId = %s", [request_user_id])
                        user_row = cursor.fetchone()
                        username = user_row[0] if user_row else f"user_{request_user_id}"
                        
                        default_role = requested_role if requested_role else 'End User'
                        
                        # Create new RBAC entry using raw SQL - use same TPRM connection
                        cursor.execute("""
                            INSERT INTO `rbac_tprm` 
                            (UserId, UserName, Role, IsActive, CreatedAt, UpdatedAt)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, [
                            request_user_id,
                            username,
                            default_role,
                            'Y',
                            timezone.now(),
                            timezone.now()
                        ])
                        
                        # Get the created entry
                        rbac_entry = RBACTPRM.objects.filter(user_id=request_user_id, is_active='Y').first()
                        logger.info(f"[TPRM Access Request] Created new RBAC entry for user {request_user_id} with role {default_role}")
                    else:
                        # Update role if requested_role is provided
                        if requested_role:
                            rbac_entry.role = requested_role
                    
                    # Map URL to permission if required_permission is not provided
                    url_to_permission_map = {
                        '/vendors': 'vendor.view_vendors',
                        '/vendor': 'vendor.view_vendors',
                        '/tprm/vendors': 'vendor.view_vendors',
                        '/contracts': 'contract.list_contracts',
                        '/contract': 'contract.list_contracts',
                        '/tprm/contracts': 'contract.list_contracts',
                        '/rfp': 'rfp.view_rfp',
                        '/rfps': 'rfp.view_rfp',
                        '/tprm/rfp': 'rfp.view_rfp',
                        '/risk': 'risk.view_identified_risks',
                        '/risks': 'risk.view_identified_risks',
                        '/tprm/risk': 'risk.view_identified_risks',
                        '/compliance': 'compliance.view_compliance_status_of_plans',
                        '/tprm/compliance': 'compliance.view_compliance_status_of_plans',
                        '/bcp-drp': 'bcpdrp.view_plans_and_documents',
                        '/bcpdrp': 'bcpdrp.view_plans_and_documents',
                        '/tprm/bcp-drp': 'bcpdrp.view_plans_and_documents',
                        '/sla': 'sla.view_sla',
                        '/slas': 'sla.view_sla',
                        '/tprm/sla': 'sla.view_sla',
                    }
                    
                    # If required_permission is empty, try to infer from URL
                    if not required_permission and requested_url:
                        # Try exact match first
                        if requested_url in url_to_permission_map:
                            required_permission = url_to_permission_map[requested_url]
                            logger.info(f"[TPRM Access Request] Inferred permission '{required_permission}' from URL '{requested_url}'")
                        else:
                            # Try partial match (e.g., /vendors/123 -> /vendors)
                            for url_pattern, perm in url_to_permission_map.items():
                                if requested_url.startswith(url_pattern):
                                    required_permission = perm
                                    logger.info(f"[TPRM Access Request] Inferred permission '{required_permission}' from URL pattern '{url_pattern}' matching '{requested_url}'")
                                    break
                    
                    # If still no permission, try to infer from requested_feature
                    if not required_permission and requested_feature:
                        feature_lower = requested_feature.lower()
                        if 'vendor' in feature_lower:
                            required_permission = 'vendor.view_vendors'
                        elif 'contract' in feature_lower:
                            required_permission = 'contract.list_contracts'
                        elif 'rfp' in feature_lower:
                            required_permission = 'rfp.view_rfp'
                        elif 'risk' in feature_lower:
                            required_permission = 'risk.view_identified_risks'
                        elif 'compliance' in feature_lower:
                            required_permission = 'compliance.view_compliance_status_of_plans'
                        elif 'bcp' in feature_lower or 'drp' in feature_lower:
                            required_permission = 'bcpdrp.view_plans_and_documents'
                        elif 'sla' in feature_lower:
                            required_permission = 'sla.view_sla'
                        
                        if required_permission:
                            logger.info(f"[TPRM Access Request] Inferred permission '{required_permission}' from feature '{requested_feature}'")
                    
                    # Map permission string to RBAC field name
                    # This mapping covers ALL TPRM permissions based on rbac_tprm table structure
                    permission_field_map = {
                        # RFP permissions
                        'rfp.create_rfp': 'create_rfp',
                        'rfp.edit_rfp': 'edit_rfp',
                        'rfp.view_rfp': 'view_rfp',
                        'rfp.delete_rfp': 'delete_rfp',
                        'rfp.clone_rfp': 'clone_rfp',
                        'rfp.submit_rfp_for_review': 'submit_rfp_for_review',
                        'rfp.approve_rfp': 'approve_rfp',
                        'rfp.reject_rfp': 'reject_rfp',
                        'rfp.assign_rfp_reviewers': 'assign_rfp_reviewers',
                        'rfp.view_rfp_approval_status': 'view_rfp_approval_status',
                        'rfp.view_rfp_versions': 'view_rfp_versions',
                        'rfp.create_rfp_version': 'create_rfp_version',
                        'rfp.edit_rfp_version': 'edit_rfp_version',
                        'rfp.view_rfp_version': 'view_rfp_version',
                        'rfp.create_evaluation_criteria': 'create_evaluation_criteria',
                        'rfp.edit_evaluation_criteria': 'edit_evaluation_criteria',
                        'rfp.delete_evaluation_criteria': 'delete_evaluation_criteria',
                        'rfp.select_vendors_for_rfp': 'select_vendors_for_rfp',
                        'rfp.invite_vendors_for_rfp': 'invite_vendors_for_rfp',
                        'rfp.track_rfp_invitations': 'track_rfp_invitations',
                        'rfp.upload_documents_for_rfp': 'upload_documents_for_rfp',
                        'rfp.download_rfp_documents': 'download_rfp_documents',
                        'rfp.preview_rfp_documents': 'preview_rfp_documents',
                        'rfp.validate_rfp_documents': 'validate_rfp_documents',
                        'rfp.scan_rfp_files_for_virus': 'scan_rfp_files_for_virus',
                        'rfp.view_rfp_responses': 'view_rfp_responses',
                        'rfp.submit_rfp_response': 'submit_rfp_response',
                        'rfp.withdraw_rfp_response': 'withdraw_rfp_response',
                        'rfp.auto_screen_rfp': 'auto_screen_rfp',
                        'rfp.assign_rfp_evaluators': 'assign_rfp_evaluators',
                        'rfp.score_rfp_response': 'score_rfp_response',
                        'rfp.view_rfp_response_scores': 'view_rfp_response_scores',
                        'rfp.rank_vendors_for_rfp': 'rank_vendors_for_rfp',
                        'rfp.finalize_rfp_evaluation': 'finalize_rfp_evaluation',
                        'rfp.send_rfp_award_notification': 'send_rfp_award_notification',
                        'rfp.view_rfp_analytics': 'view_rfp_analytics',
                        'rfp.generate_rfp_reports': 'generate_rfp_reports',
                        'rfp.download_rfp_report': 'download_rfp_report',
                        'rfp.manage_rfp_lifecycle': 'manage_rfp_lifecycle',
                        'rfp.trigger_rfp_workflow': 'trigger_rfp_workflow',
                        'rfp.escalate_rfp_workflow': 'escalate_rfp_workflow',
                        'rfp.generate_rfp_tokens': 'generate_rfp_tokens',
                        'rfp.validate_rfp_access': 'validate_rfp_access',
                        'rfp.view_rfp_audit_trail': 'view_rfp_audit_trail',
                        'rfp.send_rfp_notifications': 'send_rfp_notifications',
                        'rfp.broadcast_rfp_communications': 'broadcast_rfp_communications',
                        'rfp.clarify_rfp_communications': 'clarify_rfp_communications',
                        'rfp.amend_rfp_communications': 'amend_rfp_communications',
                        'rfp.create_rfp_vendor_from_rfp': 'create_rfp_vendor_from_rfp',
                        'rfp.match_rfp_vendor': 'match_rfp_vendor',
                        'rfp.perform_rfp_health_check': 'perform_rfp_health_check',
                        'rfp.validate_rfp_data': 'validate_rfp_data',
                        'rfp.track_rfp_activity_log': 'track_rfp_activity_log',
                        # Contract permissions
                        'contract.list_contracts': 'list_contracts',
                        'contract.create_contract': 'create_contract',
                        'contract.update_contract': 'update_contract',
                        'contract.delete_contract': 'delete_contract',
                        'contract.approve_contract': 'approve_contract',
                        'contract.reject_contract': 'reject_contract',
                        'contract.create_contract_term': 'create_contract_term',
                        'contract.list_contract_terms': 'list_contract_terms',
                        'contract.update_contract_term': 'update_contract_term',
                        'contract.delete_contract_term': 'delete_contract_term',
                        'contract.list_contract_renewals': 'list_contract_renewals',
                        'contract.create_contract_renewal': 'create_contract_renewal',
                        'contract.approve_contract_renewal': 'approve_contract_renewal',
                        'contract.reject_contract_renewal': 'reject_contract_renewal',
                        'contract.create_contract_audit': 'create_contract_audit',
                        'contract.trigger_ocr': 'trigger_ocr',
                        'contract.get_nlp_clauses': 'get_nlp_clauses',
                        'contract.contract_search': 'contract_search',
                        'contract.get_contract_history': 'get_contract_history',
                        'contract.compare_contract_version': 'compare_contract_version',
                        'contract.download_contract_document': 'download_contract_document',
                        'contract.contract_dashboard': 'contract_dashboard',
                        'contract.validate_contract_data': 'validate_contract_data',
                        # Vendor permissions
                        'vendor.view_vendors': 'view_vendors',
                        'vendor.create_vendor': 'create_vendor',
                        'vendor.update_vendor': 'update_vendor',
                        'vendor.delete_vendor': 'delete_vendor',
                        'vendor.submit_vendor_for_approval': 'submit_vendor_for_approval',
                        'vendor.approve_reject_vendor': 'approve_reject_vendor',
                        'vendor.view_contacts_documents': 'view_contacts_documents',
                        'vendor.add_update_contacts_documents': 'add_update_contacts_documents',
                        'vendor.approve_documents': 'approve_documents',
                        'vendor.view_risk_profile': 'view_risk_profile',
                        'vendor.view_lifecycle_history': 'view_lifecycle_history',
                        'vendor.manage_questionnaires': 'manage_questionnaires',
                        'vendor.view_questionnaires': 'view_questionnaires',
                        'vendor.assign_questionnaires': 'assign_questionnaires',
                        'vendor.submit_questionnaire_responses': 'submit_questionnaire_responses',
                        'vendor.review_approve_responses': 'review_approve_responses',
                        'vendor.view_risk_assessments': 'view_risk_assessments',
                        'vendor.create_risk_assessments': 'create_risk_assessments',
                        'vendor.recalculate_risk_scores': 'recalculate_risk_scores',
                        'vendor.initiate_screening': 'initiate_screening',
                        'vendor.resolve_screening_matches': 'resolve_screening_matches',
                        'vendor.view_screening_results': 'view_screening_results',
                        'vendor.view_available_vendors': 'view_available_vendors',
                        # BCP/DRP permissions
                        'bcpdrp.create_bcp_drp_strategy_and_plans': 'create_bcp_drp_strategy_and_plans',
                        'bcpdrp.view_plans_and_documents': 'view_plans_and_documents',
                        'bcpdrp.assign_plans_for_evaluation': 'assign_plans_for_evaluation',
                        'bcpdrp.approve_or_reject_plan_evaluations': 'approve_or_reject_plan_evaluations',
                        'bcpdrp.ocr_extraction_and_review': 'ocr_extraction_and_review',
                        'bcpdrp.create_questionnaire_for_testing': 'create_questionnaire_for_testing',
                        'bcpdrp.review_questionnaire_answers': 'review_questionnaire_answers',
                        'bcpdrp.final_approval_of_plan': 'final_approval_of_plan',
                        'bcpdrp.create_questionnaire': 'create_questionnaire',
                        'bcpdrp.assign_questionnaires_for_review': 'assign_questionnaires_for_review',
                        'bcpdrp.view_all_questionnaires': 'view_all_questionnaires',
                        'bcpdrp.add_vendor_to_bcp_drp_strategy': 'add_vendor_to_bcp_drp_strategy',
                        'bcpdrp.view_bcp_drp_plan_status': 'view_bcp_drp_plan_status',
                        # Risk permissions
                        'risk.assess_vendor_risk': 'assess_vendor_risk',
                        'risk.view_vendor_risk_scores': 'view_vendor_risk_scores',
                        'risk.identify_risks_in_plans': 'identify_risks_in_plans',
                        'risk.view_identified_risks': 'view_identified_risks',
                        'risk.manage_risk_mitigation_plans': 'manage_risk_mitigation_plans',
                        'risk.view_risk_mitigation_status': 'view_risk_mitigation_status',
                        # Compliance permissions
                        'compliance.view_compliance_status_of_plans': 'view_compliance_status_of_plans',
                        'compliance.audit_compliance_of_documents': 'audit_compliance_of_documents',
                        'compliance.configure_document_security_settings': 'configure_document_security_settings',
                        'compliance.view_document_access_logs': 'view_document_access_logs',
                        'compliance.review_regulatory_compliance': 'review_regulatory_compliance',
                        'compliance.audit_compliance_against_regulations': 'audit_compliance_against_regulations',
                        'compliance.review_and_approve_legal_aspects_of_plans': 'review_and_approve_legal_aspects_of_plans',
                        'compliance.generate_legal_compliance_reports': 'generate_legal_compliance_reports',
                        'compliance.view_contractual_obligations': 'view_contractual_obligations',
                        'compliance.audit_plan_documentation': 'audit_plan_documentation',
                        'compliance.view_audit_logs': 'view_audit_logs',
                        'compliance.generate_internal_audit_reports': 'generate_internal_audit_reports',
                        'compliance.conduct_external_compliance_audit': 'conduct_external_compliance_audit',
                        'compliance.generate_external_audit_reports': 'generate_external_audit_reports',
                        'compliance.review_external_auditor_comments': 'review_external_auditor_comments',
                        'compliance.audit_compliance_of_plans': 'audit_compliance_of_plans',
                        'compliance.view_compliance_audit_results': 'view_compliance_audit_results',
                        'compliance.generate_compliance_reports': 'generate_compliance_reports',
                        'compliance.generate_compliance_audit_reports': 'generate_compliance_audit_reports',
                        'compliance.view_document_status_history': 'view_document_status_history',
                        'compliance.request_document_revisions_from_vendor': 'request_document_revisions_from_vendor',
                        'compliance.view_vendor_submitted_documents': 'view_vendor_submitted_documents',
                        # System permissions
                        'system.configure_system_settings': 'configure_system_settings',
                        'system.configure_questionnaire_settings': 'configure_questionnaire_settings',
                        'system.create_update_user_roles': 'create_update_user_roles',
                        'system.manage_document_access_controls': 'manage_document_access_controls',
                        'system.manage_server_resources_for_bcp_drp': 'manage_server_resources_for_bcp_drp',
                        'system.monitor_system_health': 'monitor_system_health',
                        'system.backup_system_configuration': 'backup_system_configuration',
                        'system.view_incident_response_plans': 'view_incident_response_plans',
                        'system.create_incident_response_plans': 'create_incident_response_plans',
                        'system.update_incident_response_plans': 'update_incident_response_plans',
                        'system.integrate_bcp_drp_with_external_systems': 'integrate_bcp_drp_with_external_systems',
                        'system.manage_integration_settings': 'manage_integration_settings',
                        'system.access_integration_mappings': 'access_integration_mappings',
                        'system.initiate_sync_with_finacle': 'initiate_sync_with_finacle',
                        'system.perform_health_check': 'perform_health_check',
                        'system.test_external_connections': 'test_external_connections',
                        # SLA permissions
                        'sla.view_sla': 'view_sla',
                        'sla.create_sla': 'create_sla',
                        'sla.update_sla': 'update_sla',
                        'sla.delete_sla': 'delete_sla',
                        'sla.view_performance': 'view_performance',
                        'sla.create_performance': 'create_performance',
                        'sla.view_alerts': 'view_alerts',
                        'sla.acknowledge_resolve_alerts': 'acknowledge_resolve_alerts',
                        'sla.view_dashboard_trend': 'view_dashboard_trend',
                        'sla.activate_deactivate_sla': 'activate_deactivate_sla',
                        'sla.bulk_upload': 'bulk_upload',
                        # Vendor coordination permissions
                        'vendor.coordinate_vendor_feedback': 'coordinate_vendor_feedback',
                        'vendor.evaluate_plan_based_on_criteria': 'evaluate_plan_based_on_criteria',
                        'vendor.submit_evaluation_feedback': 'submit_evaluation_feedback',
                        'vendor.view_vendor_contracts': 'view_vendor_contracts',
                        'vendor.create_modify_contracts': 'create_modify_contracts',
                    }
                    
                    # Update permission if required_permission is provided
                    if required_permission and required_permission in permission_field_map:
                        permission_field = permission_field_map[required_permission]
                        
                        # Use raw SQL to update the rbac_tprm table directly (more reliable than ORM)
                        # Get the RBAC ID first
                        cursor.execute("""
                            SELECT RBACId FROM `rbac_tprm` 
                            WHERE UserId = %s AND IsActive = 'Y'
                            LIMIT 1
                        """, [request_user_id])
                        rbac_row = cursor.fetchone()
                        
                        if rbac_row:
                            rbac_id = rbac_row[0]
                            # Map permission field name to database column name
                            db_column_map = {
                                'create_rfp': 'CreateRFP',
                                'edit_rfp': 'EditRFP',
                                'view_rfp': 'ViewRFP',
                                'delete_rfp': 'DeleteRFP',
                                'clone_rfp': 'CloneRFP',
                                'submit_rfp_for_review': 'SubmitRFPForReview',
                                'approve_rfp': 'ApproveRFP',
                                'reject_rfp': 'RejectRFP',
                                'assign_rfp_reviewers': 'AssignRFPReviewers',
                                'view_rfp_approval_status': 'ViewRFPApprovalStatus',
                                'view_rfp_versions': 'ViewRFPVersions',
                                'create_rfp_version': 'CreateRFPVersion',
                                'edit_rfp_version': 'EditRFPVersion',
                                'view_rfp_version': 'ViewRFPVersion',
                                'create_evaluation_criteria': 'CreateEvaluationCriteria',
                                'edit_evaluation_criteria': 'EditEvaluationCriteria',
                                'delete_evaluation_criteria': 'DeleteEvaluationCriteria',
                                'select_vendors_for_rfp': 'SelectVendorsForRFP',
                                'invite_vendors_for_rfp': 'InviteVendorsForRFP',
                                'track_rfp_invitations': 'TrackRFPInvitations',
                                'upload_documents_for_rfp': 'UploadDocumentsForRFP',
                                'download_rfp_documents': 'DownloadRFPDocuments',
                                'preview_rfp_documents': 'PreviewRFPDocuments',
                                'validate_rfp_documents': 'ValidateRFPDocuments',
                                'scan_rfp_files_for_virus': 'ScanRFPFilesForVirus',
                                'view_rfp_responses': 'ViewRFPResponses',
                                'submit_rfp_response': 'SubmitRFPResponse',
                                'withdraw_rfp_response': 'WithdrawRFPResponse',
                                'auto_screen_rfp': 'AutoScreenRFP',
                                'assign_rfp_evaluators': 'AssignRFPEvaluators',
                                'score_rfp_response': 'ScoreRFPResponse',
                                'view_rfp_response_scores': 'ViewRFPResponseScores',
                                'rank_vendors_for_rfp': 'RankVendorsForRFP',
                                'finalize_rfp_evaluation': 'FinalizeRFPEvaluation',
                                'send_rfp_award_notification': 'SendRFPAwardNotification',
                                'view_rfp_analytics': 'ViewRFPAnalytics',
                                'generate_rfp_reports': 'GenerateRFPReports',
                                'download_rfp_report': 'DownloadRFPReport',
                                'manage_rfp_lifecycle': 'ManageRFPLifecycle',
                                'trigger_rfp_workflow': 'TriggerRFPWorkflow',
                                'escalate_rfp_workflow': 'EscalateRFPWorkflow',
                                'generate_rfp_tokens': 'GenerateRFPTokens',
                                'validate_rfp_access': 'ValidateRFPAccess',
                                'view_rfp_audit_trail': 'ViewRFPAuditTrail',
                                'send_rfp_notifications': 'SendRFPNotifications',
                                'broadcast_rfp_communications': 'BroadcastRFPCommunications',
                                'clarify_rfp_communications': 'ClarifyRFPCommunications',
                                'amend_rfp_communications': 'AmendRFPCommunications',
                                'create_rfp_vendor_from_rfp': 'CreateRFPVendorFromRFP',
                                'match_rfp_vendor': 'MatchRFPVendor',
                                'perform_rfp_health_check': 'PerformRFPHealthCheck',
                                'validate_rfp_data': 'ValidateRFPData',
                                'track_rfp_activity_log': 'TrackRFPActivityLog',
                                'list_contracts': 'ListContracts',
                                'create_contract': 'CreateContract',
                                'update_contract': 'UpdateContract',
                                'delete_contract': 'DeleteContract',
                                'approve_contract': 'ApproveContract',
                                'reject_contract': 'RejectContract',
                                'create_contract_term': 'CreateContractTerm',
                                'list_contract_terms': 'ListContractTerms',
                                'update_contract_term': 'UpdateContractTerm',
                                'delete_contract_term': 'DeleteContractTerm',
                                'list_contract_renewals': 'ListContractRenewals',
                                'create_contract_renewal': 'CreateContractRenewal',
                                'approve_contract_renewal': 'ApproveContractRenewal',
                                'reject_contract_renewal': 'RejectContractRenewal',
                                'create_contract_audit': 'CreateContractAudit',
                                'trigger_ocr': 'TriggerOCR',
                                'get_nlp_clauses': 'GetNLPClauses',
                                'contract_search': 'ContractSearch',
                                'get_contract_history': 'GetContractHistory',
                                'compare_contract_version': 'CompareContractVersion',
                                'download_contract_document': 'DownloadContractDocument',
                                'contract_dashboard': 'ContractDashboard',
                                'validate_contract_data': 'ValidateContractData',
                                'view_vendors': 'ViewVendors',
                                'create_vendor': 'CreateVendor',
                                'update_vendor': 'UpdateVendor',
                                'delete_vendor': 'DeleteVendor',
                                'submit_vendor_for_approval': 'SubmitVendorForApproval',
                                'approve_reject_vendor': 'ApproveRejectVendor',
                                'view_contacts_documents': 'ViewContactsDocuments',
                                'add_update_contacts_documents': 'AddUpdateContactsDocuments',
                                'approve_documents': 'ApproveDocuments',
                                'view_risk_profile': 'ViewRiskProfile',
                                'view_lifecycle_history': 'ViewLifecycleHistory',
                                'manage_questionnaires': 'ManageQuestionnaires',
                                'view_questionnaires': 'ViewQuestionnaires',
                                'assign_questionnaires': 'AssignQuestionnaires',
                                'submit_questionnaire_responses': 'SubmitQuestionnaireResponses',
                                'review_approve_responses': 'ReviewApproveResponses',
                                'view_risk_assessments': 'ViewRiskAssessments',
                                'create_risk_assessments': 'CreateRiskAssessments',
                                'recalculate_risk_scores': 'RecalculateRiskScores',
                                'initiate_screening': 'InitiateScreening',
                                'resolve_screening_matches': 'ResolveScreeningMatches',
                                'view_screening_results': 'ViewScreeningResults',
                                'view_available_vendors': 'ViewAvailableVendors',
                                'create_bcp_drp_strategy_and_plans': 'CreateBCPDRPStrategyAndPlans',
                                'view_plans_and_documents': 'ViewPlansAndDocuments',
                                'assign_plans_for_evaluation': 'AssignPlansForEvaluation',
                                'approve_or_reject_plan_evaluations': 'ApproveOrRejectPlanEvaluations',
                                'ocr_extraction_and_review': 'OCRExtractionAndReview',
                                'create_questionnaire_for_testing': 'CreateQuestionnaireForTesting',
                                'review_questionnaire_answers': 'ReviewQuestionnaireAnswers',
                                'final_approval_of_plan': 'FinalApprovalOfPlan',
                                'create_questionnaire': 'CreateQuestionnaire',
                                'assign_questionnaires_for_review': 'AssignQuestionnairesForReview',
                                'view_all_questionnaires': 'ViewAllQuestionnaires',
                                'add_vendor_to_bcp_drp_strategy': 'AddVendorToBCPDRPStrategy',
                                'view_bcp_drp_plan_status': 'ViewBCPDRPPlanStatus',
                                'assess_vendor_risk': 'AssessVendorRisk',
                                'view_vendor_risk_scores': 'ViewVendorRiskScores',
                                'identify_risks_in_plans': 'IdentifyRisksInPlans',
                                'view_identified_risks': 'ViewIdentifiedRisks',
                                'manage_risk_mitigation_plans': 'ManageRiskMitigationPlans',
                                'view_risk_mitigation_status': 'ViewRiskMitigationStatus',
                                'view_compliance_status_of_plans': 'ViewComplianceStatusOfPlans',
                                'audit_compliance_of_documents': 'AuditComplianceOfDocuments',
                                'configure_document_security_settings': 'ConfigureDocumentSecuritySettings',
                                'view_document_access_logs': 'ViewDocumentAccessLogs',
                                'review_regulatory_compliance': 'ReviewRegulatoryCompliance',
                                'audit_compliance_against_regulations': 'AuditComplianceAgainstRegulations',
                                'review_and_approve_legal_aspects_of_plans': 'ReviewAndApproveLegalAspectsOfPlans',
                                'generate_legal_compliance_reports': 'GenerateLegalComplianceReports',
                                'view_contractual_obligations': 'ViewContractualObligations',
                                'audit_plan_documentation': 'AuditPlanDocumentation',
                                'view_audit_logs': 'ViewAuditLogs',
                                'generate_internal_audit_reports': 'GenerateInternalAuditReports',
                                'conduct_external_compliance_audit': 'ConductExternalComplianceAudit',
                                'generate_external_audit_reports': 'GenerateExternalAuditReports',
                                'review_external_auditor_comments': 'ReviewExternalAuditorComments',
                                'audit_compliance_of_plans': 'AuditComplianceOfPlans',
                                'view_compliance_audit_results': 'ViewComplianceAuditResults',
                                'generate_compliance_reports': 'GenerateComplianceReports',
                                'generate_compliance_audit_reports': 'GenerateComplianceAuditReports',
                                'view_document_status_history': 'ViewDocumentStatusHistory',
                                'request_document_revisions_from_vendor': 'RequestDocumentRevisionsFromVendor',
                                'view_vendor_submitted_documents': 'ViewVendorSubmittedDocuments',
                                'configure_system_settings': 'ConfigureSystemSettings',
                                'configure_questionnaire_settings': 'ConfigureQuestionnaireSettings',
                                'create_update_user_roles': 'CreateUpdateUserRoles',
                                'manage_document_access_controls': 'ManageDocumentAccessControls',
                                'manage_server_resources_for_bcp_drp': 'ManageServerResourcesForBCPDRP',
                                'monitor_system_health': 'MonitorSystemHealth',
                                'backup_system_configuration': 'BackupSystemConfiguration',
                                'view_incident_response_plans': 'ViewIncidentResponsePlans',
                                'create_incident_response_plans': 'CreateIncidentResponsePlans',
                                'update_incident_response_plans': 'UpdateIncidentResponsePlans',
                                'integrate_bcp_drp_with_external_systems': 'IntegrateBCPDRPWithExternalSystems',
                                'manage_integration_settings': 'ManageIntegrationSettings',
                                'access_integration_mappings': 'AccessIntegrationMappings',
                                'initiate_sync_with_finacle': 'InitiateSyncWithFinacle',
                                'perform_health_check': 'PerformHealthCheck',
                                'test_external_connections': 'TestExternalConnections',
                                'view_sla': 'ViewSLA',
                                'create_sla': 'CreateSLA',
                                'update_sla': 'UpdateSLA',
                                'delete_sla': 'DeleteSLA',
                                'view_performance': 'ViewPerformance',
                                'create_performance': 'CreatePerformance',
                                'view_alerts': 'ViewAlerts',
                                'acknowledge_resolve_alerts': 'AcknowledgeResolveAlerts',
                                'view_dashboard_trend': 'ViewDashboardTrend',
                                'activate_deactivate_sla': 'ActivateDeactivateSLA',
                                'bulk_upload': 'BulkUpload',
                                'coordinate_vendor_feedback': 'CoordinateVendorFeedback',
                                'evaluate_plan_based_on_criteria': 'EvaluatePlanBasedOnCriteria',
                                'submit_evaluation_feedback': 'SubmitEvaluationFeedback',
                                'view_vendor_contracts': 'ViewVendorContracts',
                                'create_modify_contracts': 'CreateModifyContracts',
                            }
                            
                            db_column = db_column_map.get(permission_field)
                            if db_column:
                                # Update the permission field to 1 (True) using raw SQL
                                cursor.execute(f"""
                                    UPDATE `rbac_tprm` 
                                    SET `{db_column}` = 1,
                                        `UpdatedAt` = %s
                                    WHERE `RBACId` = %s
                                """, [timezone.now(), rbac_id])
                                
                                # Commit the transaction explicitly to ensure the update is persisted
                                tprm_connection.commit()
                                logger.debug(f"[TPRM Access Request] Committed permission update transaction")
                                
                                # Verify the update was successful
                                cursor.execute(f"""
                                    SELECT `{db_column}` FROM `rbac_tprm` 
                                    WHERE `RBACId` = %s
                                """, [rbac_id])
                                verify_row = cursor.fetchone()
                                if verify_row and verify_row[0] == 1:
                                    logger.info(f"[TPRM Access Request] Verified: Permission {required_permission} ({permission_field} -> {db_column}) successfully set to 1 for user {request_user_id}")
                                else:
                                    logger.warning(f"[TPRM Access Request] Warning: Permission update may not have taken effect. Value: {verify_row[0] if verify_row else 'None'}")
                                
                                # Aggressively clear all caches to ensure fresh permission checks
                                try:
                                    from django.core.cache import cache
                                    # Clear specific user cache
                                    cache_key = f"rbac_tprm_user_{request_user_id}"
                                    cache.delete(cache_key)
                                    logger.debug(f"[TPRM Access Request] Cleared cache key: {cache_key}")
                                    
                                    # Clear any vendor permission caches
                                    vendor_cache_keys = [
                                        f"vendor_user_permissions_{request_user_id}",
                                        f"rbac_vendor_{request_user_id}",
                                        f"permissions_user_{request_user_id}"
                                    ]
                                    for key in vendor_cache_keys:
                                        cache.delete(key)
                                        logger.debug(f"[TPRM Access Request] Cleared cache key: {key}")
                                    
                                    # Clear all cache patterns that might contain permission data
                                    try:
                                        # If using a cache backend that supports pattern deletion
                                        cache.clear()  # Nuclear option - clears all cache
                                        logger.info(f"[TPRM Access Request] Cleared all cache to ensure fresh permission checks")
                                    except Exception:
                                        # If clear() is not supported, just log
                                        logger.debug(f"[TPRM Access Request] Cache clear() not supported, using individual key deletion")
                                        
                                except Exception as cache_error:
                                    logger.warning(f"[TPRM Access Request] Could not clear cache: {cache_error}")
                                
                                logger.info(f"[TPRM Access Request] Granted permission {required_permission} ({permission_field} -> {db_column}) to user {request_user_id} via SQL UPDATE")
                                
                                # Note: We don't close the connection here because we still need it for the final UPDATE
                                # The connection will be closed after all operations are complete
                                
                                # Test that the permission check now works (with force_refresh to bypass cache)
                                try:
                                    # Use the already-imported RBACTPRMUtils from module level
                                    # Test the permission check with force_refresh to ensure it reads fresh data
                                    # Wait a tiny bit to ensure database transaction is committed
                                    import time
                                    time.sleep(0.1)  # Small delay to ensure DB commit
                                    
                                    # Test with vendor permission check (which is what the frontend uses)
                                    # Test both the direct permission check and the vendor permission check
                                    test_permission_direct = RBACTPRMUtils.check_permission(request_user_id, permission_field, force_refresh=True)
                                    test_permission_vendor = RBACTPRMUtils.check_vendor_permission(request_user_id, 'view_vendors', force_refresh=True)
                                    
                                    if test_permission_direct and test_permission_vendor:
                                        logger.info(f"[TPRM Access Request] ✅✅✅ SUCCESS: Both permission checks passed - User {request_user_id} now has view_vendors permission and can access vendor pages immediately")
                                        audit_trail['rbac_permission_verified'] = True
                                        audit_trail['rbac_permission_test_result'] = 'PASSED'
                                        audit_trail['rbac_direct_check'] = True
                                        audit_trail['rbac_vendor_check'] = True
                                    elif test_permission_direct:
                                        logger.warning(f"[TPRM Access Request] ⚠️ PARTIAL: Direct permission check passed but vendor permission check failed for user {request_user_id}")
                                        audit_trail['rbac_permission_verified'] = False
                                        audit_trail['rbac_permission_test_result'] = 'PARTIAL'
                                        audit_trail['rbac_direct_check'] = True
                                        audit_trail['rbac_vendor_check'] = False
                                    elif test_permission_vendor:
                                        logger.warning(f"[TPRM Access Request] ⚠️ PARTIAL: Vendor permission check passed but direct permission check failed for user {request_user_id}")
                                        audit_trail['rbac_permission_verified'] = False
                                        audit_trail['rbac_permission_test_result'] = 'PARTIAL'
                                        audit_trail['rbac_direct_check'] = False
                                        audit_trail['rbac_vendor_check'] = True
                                    else:
                                        logger.warning(f"[TPRM Access Request] ⚠️ WARNING: Both permission checks failed - User {request_user_id} does not have view_vendors permission after update")
                                        audit_trail['rbac_permission_verified'] = False
                                        audit_trail['rbac_permission_test_result'] = 'FAILED'
                                        audit_trail['rbac_direct_check'] = False
                                        audit_trail['rbac_vendor_check'] = False
                                        
                                        # Double-check with raw SQL
                                        try:
                                            with tprm_connection.cursor() as verify_cursor:
                                                verify_cursor.execute(f"""
                                                    SELECT `{db_column}` FROM `rbac_tprm` 
                                                    WHERE UserId = %s AND IsActive = 'Y'
                                                """, [request_user_id])
                                                verify_result = verify_cursor.fetchone()
                                                if verify_result and verify_result[0] == 1:
                                                    logger.warning(f"[TPRM Access Request] ⚠️ Raw SQL confirms permission is set to 1, but permission check returned False. This indicates a cache or mapping issue.")
                                                    audit_trail['rbac_orm_cache_issue'] = True
                                                    audit_trail['rbac_raw_sql_value'] = verify_result[0]
                                                else:
                                                    logger.error(f"[TPRM Access Request] ❌ ERROR: Raw SQL shows permission is NOT set. Value: {verify_result[0] if verify_result else 'None'}")
                                                    audit_trail['rbac_raw_sql_value'] = verify_result[0] if verify_result else None
                                        except Exception as sql_error:
                                            logger.warning(f"[TPRM Access Request] Could not verify with raw SQL: {sql_error}")
                                            
                                except Exception as test_error:
                                    logger.error(f"[TPRM Access Request] ❌ ERROR: Could not verify permission check: {test_error}")
                                    import traceback
                                    logger.error(f"[TPRM Access Request] Traceback: {traceback.format_exc()}")
                                    audit_trail['rbac_permission_verification_error'] = str(test_error)
                                
                                # Note: We don't close the connection here because we still need it for the final UPDATE
                                # The connection will be automatically managed by Django's connection pooling
                                
                                audit_trail['rbac_permission_granted'] = required_permission
                                audit_trail['rbac_permission_field'] = permission_field
                                audit_trail['rbac_db_column'] = db_column
                                audit_trail['rbac_updated_via_sql'] = True
                                audit_trail['rbac_verified'] = verify_row[0] == 1 if verify_row else False
                            else:
                                logger.warning(f"[TPRM Access Request] Database column not found for permission field {permission_field}")
                                audit_trail['rbac_permission_error'] = f"Database column not found for permission field {permission_field}"
                        else:
                            logger.error(f"[TPRM Access Request] RBAC entry not found for user {request_user_id}")
                            audit_trail['rbac_permission_error'] = f"RBAC entry not found for user {request_user_id}"
                    elif required_permission:
                        logger.warning(f"[TPRM Access Request] Unknown permission format: {required_permission}")
                        audit_trail['rbac_permission_error'] = f"Unknown permission format: {required_permission}"
                    else:
                        logger.warning(f"[TPRM Access Request] No permission to grant - required_permission is empty and could not be inferred from URL/feature")
                        audit_trail['rbac_permission_error'] = "No permission specified and could not be inferred from URL or feature"
                    
                    audit_trail['rbac_updated'] = True
                    # Get role from database directly to avoid ORM cache
                    try:
                        cursor.execute("SELECT Role FROM `rbac_tprm` WHERE UserId = %s AND IsActive = 'Y' LIMIT 1", [request_user_id])
                        role_row = cursor.fetchone()
                        audit_trail['rbac_role'] = role_row[0] if role_row else (rbac_entry.role if rbac_entry else 'Unknown')
                    except Exception:
                        audit_trail['rbac_role'] = rbac_entry.role if rbac_entry else 'Unknown'
                    audit_trail['rbac_updated_at'] = updated_at.isoformat()
                    logger.info(f"[TPRM Access Request] Updated RBAC entry for user {request_user_id}")
                    
                    # Force refresh ORM model instance if it exists
                    if rbac_entry:
                        try:
                            # Refresh from database to get latest values
                            rbac_entry.refresh_from_db()
                            logger.debug(f"[TPRM Access Request] Refreshed ORM model instance for user {request_user_id}")
                        except Exception as refresh_error:
                            logger.debug(f"[TPRM Access Request] Could not refresh ORM model: {refresh_error}")
                    
                except Exception as e:
                    logger.error(f"[TPRM Access Request] Error updating RBAC for access request {request_id}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    audit_trail['rbac_update_error'] = str(e)
            elif new_status_upper == 'REJECTED':
                # Explicitly log that RBAC is NOT being updated for rejected requests
                logger.info(f"[TPRM Access Request] Access request {request_id} rejected - RBAC table will NOT be updated (permissions remain unchanged)")
                audit_trail['rbac_update_skipped'] = True
                audit_trail['rbac_update_reason'] = 'Request rejected - permissions unchanged'
            
            # Update the request status in AccessRequestTPRM table - use TPRM database connection
            # Wrap in try-except to handle case where cursor might be invalid if connection was closed
            try:
                if new_status_upper == 'APPROVED':
                    cursor.execute("""
                        UPDATE `AccessRequestTPRM`
                        SET status = %s,
                            updated_at = %s,
                            audit_trail = %s,
                            approved_by = %s
                        WHERE id = %s
                    """, [new_status_upper, updated_at, json.dumps(audit_trail), user_id_int, request_id])
                else:
                    cursor.execute("""
                        UPDATE `AccessRequestTPRM`
                        SET status = %s,
                            updated_at = %s,
                            audit_trail = %s
                        WHERE id = %s
                    """, [new_status_upper, updated_at, json.dumps(audit_trail), request_id])
            except Exception as cursor_error:
                # If cursor is invalid (e.g., connection was closed), get a new cursor
                logger.warning(f"[TPRM Access Request] Cursor error during final update, getting new cursor: {cursor_error}")
                with tprm_connection.cursor() as new_cursor:
                    if new_status_upper == 'APPROVED':
                        new_cursor.execute("""
                            UPDATE `AccessRequestTPRM`
                            SET status = %s,
                                updated_at = %s,
                                audit_trail = %s,
                                approved_by = %s
                            WHERE id = %s
                        """, [new_status_upper, updated_at, json.dumps(audit_trail), user_id_int, request_id])
                    else:
                        new_cursor.execute("""
                            UPDATE `AccessRequestTPRM`
                            SET status = %s,
                                updated_at = %s,
                                audit_trail = %s
                            WHERE id = %s
                        """, [new_status_upper, updated_at, json.dumps(audit_trail), request_id])
            
            logger.info(f"[TPRM Access Request] Access request {request_id} {new_status.lower()} by user {user_id_int}")
            
            # Commit all changes and close connection to ensure fresh queries for next request
            try:
                tprm_connection.commit()
                logger.debug(f"[TPRM Access Request] Committed all database changes")
            except Exception as commit_error:
                logger.debug(f"[TPRM Access Request] Commit note: {commit_error}")
            
            # Close connection after all operations to force fresh queries
            try:
                tprm_connection.close()
                logger.debug(f"[TPRM Access Request] Closed database connection after all operations")
            except Exception as conn_error:
                logger.debug(f"[TPRM Access Request] Connection close note: {conn_error}")
            
            return Response({
                'status': 'success',
                'message': f'Request {new_status.lower()} successfully',
                'data': {
                    'id': request_id,
                    'status': new_status,
                    'updated_at': updated_at.isoformat()
                }
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"[TPRM Access Request] Error updating access request status: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'status': 'error', 'message': f'Failed to update request: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

