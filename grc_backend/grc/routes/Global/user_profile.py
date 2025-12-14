import logging
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from ...models import Users, Department, BusinessUnit, Entity, Location, DataSubjectRequest, RBAC, AccessRequest, Framework
from ...rbac.utils import RBACUtils

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def get_user_business_info(request, user_id):
    try:
        # Get user's department ID
        user = Users.objects.get(UserId=user_id)
        department_id = user.DepartmentId

        # Get department info with related data using raw SQL for efficient joins
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    d.DepartmentName,
                    d.DepartmentHead,
                    bu.Name as BusinessUnitName,
                    e.EntityName,
                    CONCAT(l.AddressLine, ', ', l.City, ', ', l.State, ', ', l.Country) as Location
                FROM department d
                LEFT JOIN businessunits bu ON d.BusinessUnitId = bu.BusinessUnitId
                LEFT JOIN mainentities e ON d.EntityId = e.Id
                LEFT JOIN locations l ON e.LocationId = l.LocationID
                WHERE d.DepartmentId = %s
            """, [department_id])
            
            columns = [col[0] for col in cursor.description]
            result = dict(zip(columns, cursor.fetchone()))

            # Get department head name
            if result['DepartmentHead']:
                dept_head = Users.objects.filter(UserId=result['DepartmentHead']).first()
                if dept_head:
                    result['DepartmentHead'] = f"{dept_head.FirstName} {dept_head.LastName}"

        return JsonResponse({
            'status': 'success',
            'data': result
        })

    except Users.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_user_profile(request, user_id):
    try:
        logger.debug(f"Fetching user profile for user_id: {user_id}")
        user = Users.objects.get(UserId=user_id)
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'firstName': user.FirstName,
                'lastName': user.LastName,
                'email': user.Email,
                'username': user.UserName,
                'isActive': user.IsActive,
                'departmentId': user.DepartmentId
            }
        })

    except Users.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500) 




@api_view(['GET'])
def get_current_user(request):
    """
    Returns the current logged-in user's details including their role from session
    """
    try:
        # Get user details from session using RBAC utils
        user_id = RBACUtils.get_user_id_from_request(request)
        
        if not user_id:
            return Response(
                {'error': 'User not authenticated or session expired'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get RBAC record which contains role and username
        rbac_record = RBACUtils.get_user_rbac_record(user_id)
        
        if not rbac_record:
            return Response(
                {'error': 'No RBAC record found for user'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user_data = {
            'UserId': user_id,
            'UserName': rbac_record.username,
            'role': rbac_record.role,
            'permissions': RBACUtils.get_user_permissions_summary(user_id)
        }
        
        print("Constructed user_data:", user_data)
        
        return Response(user_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch user details: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_data_subject_requests(request, user_id):
    """
    Get data subject requests for a user.
    If the user is a GRC Administrator, show all requests.
    Otherwise, show only the user's own requests.
    """
    try:
        # Verify user exists
        user = Users.objects.get(UserId=user_id)
        
        # Check if user is GRC Administrator
        is_admin = False
        try:
            rbac_record = RBACUtils.get_user_rbac_record(user_id)
            if rbac_record and rbac_record.role == 'GRC Administrator':
                is_admin = True
        except Exception as e:
            logger.warning(f"Could not check RBAC for user {user_id}: {str(e)}")
        
        # Use raw SQL to query the table with exact case-sensitive name
        # This works around Django's table name lowercasing issue
        with connection.cursor() as cursor:
            if is_admin:
                # Admin sees all requests
                cursor.execute("""
                    SELECT 
                        dsr.id,
                        dsr.request_type,
                        dsr.user_id,
                        dsr.status,
                        dsr.created_at,
                        dsr.updated_at,
                        dsr.verification_status,
                        dsr.audit_trail,
                        dsr.expiration_date,
                        dsr.approved_by,
                        u.FirstName,
                        u.LastName,
                        approver.FirstName as ApproverFirstName,
                        approver.LastName as ApproverLastName
                    FROM `DataSubjectRequest` dsr
                    LEFT JOIN `users` u ON dsr.user_id = u.UserId
                    LEFT JOIN `users` approver ON dsr.approved_by = approver.UserId
                    ORDER BY dsr.created_at DESC
                """)
            else:
                # Regular user sees only their own requests
                cursor.execute("""
                    SELECT 
                        dsr.id,
                        dsr.request_type,
                        dsr.user_id,
                        dsr.status,
                        dsr.created_at,
                        dsr.updated_at,
                        dsr.verification_status,
                        dsr.audit_trail,
                        dsr.expiration_date,
                        dsr.approved_by,
                        approver.FirstName as ApproverFirstName,
                        approver.LastName as ApproverLastName
                    FROM `DataSubjectRequest` dsr
                    LEFT JOIN `users` approver ON dsr.approved_by = approver.UserId
                    WHERE dsr.user_id = %s
                    ORDER BY dsr.created_at DESC
                """, [user_id])
            
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            
            # Map request type to display names
            request_type_map = {
                'ACCESS': 'Access',
                'RECTIFICATION': 'Rectification',
                'ERASURE': 'Erasure',
                'PORTABILITY': 'Portability'
            }
            
            # Map status to display names
            status_map = {
                'REQUESTED': 'Requested',
                'APPROVED': 'Approved',
                'REJECTED': 'Rejected'
            }
            
            # Map verification status to display names
            verification_status_map = {
                'NOT VERIFIED': 'Not Verified',
                'VERIFIED': 'Verified'
            }
            
            # Serialize the data
            requests_data = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                # Get user name - use from join if admin, otherwise use current user
                if is_admin and 'FirstName' in row_dict and 'LastName' in row_dict:
                    user_name = f"{row_dict.get('FirstName', '')} {row_dict.get('LastName', '')}".strip()
                    if not user_name:
                        # Fallback: fetch user if name not in result
                        try:
                            req_user = Users.objects.get(UserId=row_dict['user_id'])
                            user_name = f"{req_user.FirstName} {req_user.LastName}"
                        except:
                            user_name = f"User {row_dict['user_id']}"
                else:
                    user_name = f"{user.FirstName} {user.LastName}"
                
                # Get approver name if approved_by exists
                approved_by_name = None
                if row_dict.get('approved_by'):
                    # Check if approver name is in the result (from JOIN)
                    if 'ApproverFirstName' in row_dict and 'ApproverLastName' in row_dict:
                        approver_first = row_dict.get('ApproverFirstName', '')
                        approver_last = row_dict.get('ApproverLastName', '')
                        if approver_first or approver_last:
                            approved_by_name = f"{approver_first} {approver_last}".strip()
                    
                    # Fallback: fetch approver user if name not in result
                    if not approved_by_name:
                        try:
                            approver_user = Users.objects.get(UserId=row_dict['approved_by'])
                            approved_by_name = f"{approver_user.FirstName} {approver_user.LastName}"
                        except:
                            approved_by_name = f"User {row_dict['approved_by']}"
                
                # Parse JSON audit_trail if it exists
                audit_trail = row_dict.get('audit_trail')
                if isinstance(audit_trail, str):
                    try:
                        audit_trail = json.loads(audit_trail)
                    except:
                        audit_trail = {}
                elif audit_trail is None:
                    audit_trail = {}
                
                requests_data.append({
                    'id': row_dict['id'],
                    'request_type': row_dict['request_type'],
                    'request_type_display': request_type_map.get(row_dict['request_type'], row_dict['request_type']),
                    'user_id': row_dict['user_id'],
                    'user_name': user_name,
                    'status': row_dict['status'],
                    'status_display': status_map.get(row_dict['status'], row_dict['status']),
                    'created_at': row_dict['created_at'].isoformat() if row_dict['created_at'] else None,
                    'updated_at': row_dict['updated_at'].isoformat() if row_dict['updated_at'] else None,
                    'verification_status': row_dict['verification_status'],
                    'verification_status_display': verification_status_map.get(row_dict['verification_status'], row_dict['verification_status']),
                    'audit_trail': audit_trail,
                    'expiration_date': row_dict['expiration_date'].isoformat() if row_dict.get('expiration_date') else None,
                    'approved_by': row_dict.get('approved_by'),
                    'approved_by_name': approved_by_name,
                })
        
        return Response({
            'status': 'success',
            'data': requests_data,
            'count': len(requests_data),
            'is_admin': is_admin
        }, status=status.HTTP_200_OK)
        
    except Users.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error fetching data subject requests: {str(e)}")
        return Response(
            {'status': 'error', 'message': f'Failed to fetch requests: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@csrf_exempt
@authentication_classes([])  # Allow both authenticated and unauthenticated requests
@permission_classes([AllowAny])
def create_data_subject_request(request):
    """
    Create a new data subject request (Access, Rectification, Erasure, Portability)
    """
    try:
        # Get user ID from request
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response(
                {'status': 'error', 'message': 'User not authenticated'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get request data
        request_type = request.data.get('request_type')
        changes = request.data.get('changes', {})
        info_type = request.data.get('info_type', 'personal')  # 'personal' or 'business'
        audit_trail_data = request.data.get('audit_trail', {})  # For ACCESS type requests
        
        # Validate request type
        valid_types = ['ACCESS', 'RECTIFICATION', 'ERASURE', 'PORTABILITY']
        if request_type not in valid_types:
            return Response(
                {'status': 'error', 'message': f'Invalid request type. Must be one of: {", ".join(valid_types)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user to find framework
        user = Users.objects.get(UserId=user_id)
        framework = getattr(user, 'FrameworkId', None)
        if not framework:
            framework = Framework.objects.filter(Status='Approved', ActiveInactive='Active').first()
        
        # Create audit trail
        if request_type == 'ACCESS':
            # For ACCESS type, use the provided audit_trail data (contains requested_url, required_permission, etc.)
            audit_trail = audit_trail_data.copy() if audit_trail_data else {}
            audit_trail['request_type'] = request_type
            audit_trail['requested_at'] = timezone.now().isoformat()
            audit_trail['requested_by'] = user_id
        else:
            # For other types (RECTIFICATION, ERASURE, PORTABILITY), use the standard format
            audit_trail = {
                'request_type': request_type,
                'info_type': info_type,
                'changes': changes,
                'requested_at': timezone.now().isoformat(),
                'requested_by': user_id
            }
        
        # Check if FrameworkId column exists in the database table
        # If it doesn't exist, we'll create the request without it
        framework_id_value = framework.FrameworkId if framework else None
        
        # Create the data subject request using raw SQL to avoid Django ORM issues
        with connection.cursor() as cursor:
            # First, check if FrameworkId column exists
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'DataSubjectRequest' 
                AND COLUMN_NAME = 'FrameworkId'
            """)
            has_framework_id = cursor.fetchone() is not None
            
            if has_framework_id and framework_id_value:
                # Include FrameworkId in the INSERT
                cursor.execute("""
                    INSERT INTO `DataSubjectRequest` 
                    (request_type, user_id, status, verification_status, audit_trail, approved_by, FrameworkId, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    request_type,
                    user_id,
                    'REQUESTED',
                    'NOT VERIFIED',
                    json.dumps(audit_trail),
                    None,  # approved_by is NULL initially
                    framework_id_value,
                    timezone.now(),
                    timezone.now()
                ])
            else:
                # FrameworkId column doesn't exist, create without it
                cursor.execute("""
                    INSERT INTO `DataSubjectRequest` 
                    (request_type, user_id, status, verification_status, audit_trail, approved_by, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    request_type,
                    user_id,
                    'REQUESTED',
                    'NOT VERIFIED',
                    json.dumps(audit_trail),
                    None,  # approved_by is NULL initially
                    timezone.now(),
                    timezone.now()
                ])
            
            request_id = cursor.lastrowid
        
        logger.info(f"Data subject request {request_id} created by user {user_id} for {request_type}")
        
        return Response({
            'status': 'success',
            'message': f'{request_type} request created successfully',
            'data': {
                'id': request_id,
                'request_type': request_type,
                'status': 'REQUESTED',
                'created_at': timezone.now().isoformat()
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating data subject request: {str(e)}")
        return Response(
            {'status': 'error', 'message': f'Failed to create request: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['PUT'])
@authentication_classes([])  # Allow both authenticated and unauthenticated requests
@permission_classes([AllowAny])
def update_data_subject_request_status(request, request_id):
    """
    Update the status of a data subject request (Approve/Reject)
    Only GRC Administrators can approve/reject requests
    """
    try:
        # Get the request
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, status
                FROM `DataSubjectRequest`
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
            
            # Get the user making the update from request (JWT or session)
            user_id = RBACUtils.get_user_id_from_request(request)
            logger.info(f"User ID from RBACUtils: {user_id}, type: {type(user_id)}")
            
            if not user_id:
                # Fallback to request data if not in JWT/session
                user_id = request.data.get('user_id')
                logger.info(f"User ID from request data: {user_id}")
                if not user_id:
                    return Response(
                        {'status': 'error', 'message': 'User not authenticated'}, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            
            # Check if user is an admin (user IDs 1, 2, 3, or 4)
            admin_user_ids = [1, 2, 3, 4]
            try:
                user_id_int = int(user_id)
                is_admin = user_id_int in admin_user_ids
                logger.info(f"User ID {user_id_int} is admin: {is_admin}, admin list: {admin_user_ids}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Error converting user_id to int: {e}, user_id: {user_id}")
                is_admin = False
            
            if not is_admin:
                logger.warning(f"Access denied for user {user_id} - not in admin list {admin_user_ids}")
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
            
            # Validate status - use uppercase to match database values
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
            
            # Get apply_changes flag
            apply_changes = request.data.get('apply_changes', False)
            
            # Update the request status
            updated_at = timezone.now()
            
            # Get current audit trail, request type, and request details
            cursor.execute("""
                SELECT audit_trail, user_id, request_type
                FROM `DataSubjectRequest`
                WHERE id = %s
            """, [request_id])
            
            audit_row = cursor.fetchone()
            audit_trail = {}
            request_user_id = None
            request_type = None
            if audit_row:
                request_user_id = audit_row[1]
                request_type = audit_row[2]
                if audit_row[0]:
                    if isinstance(audit_row[0], str):
                        try:
                            audit_trail = json.loads(audit_row[0])
                        except:
                            audit_trail = {}
                    elif isinstance(audit_row[0], dict):
                        audit_trail = audit_row[0]
            
            # Handle ACCESS type requests - update RBAC when approved
            if request_type == 'ACCESS' and new_status_upper == 'APPROVED':
                try:
                    logger.info(f"Processing RBAC update for approved ACCESS request {request_id}, user {request_user_id}")
                    
                    # Extract access request data from audit_trail
                    required_permission = audit_trail.get('required_permission', '')
                    requested_role = audit_trail.get('requested_role', '')
                    requested_url = audit_trail.get('requested_url', '')
                    
                    # Get user
                    user = Users.objects.get(UserId=request_user_id)
                    
                    # Get or create framework - use user's framework or first available
                    framework = getattr(user, 'FrameworkId', None)
                    if not framework:
                        framework = Framework.objects.filter(Status='Approved', ActiveInactive='Active').first()
                    
                    if not framework:
                        logger.warning(f"No framework found for access request {request_id}")
                        audit_trail['rbac_update_error'] = 'No framework found'
                    else:
                        # Map permission string (module.permission) to RBAC field name
                        # This mapping covers ALL modules and ALL permissions in the system
                        permission_field_map = {
                            # Compliance permissions
                            'compliance.create_compliance': 'create_compliance',
                            'compliance.edit_compliance': 'edit_compliance',
                            'compliance.approve_compliance': 'approve_compliance',
                            'compliance.view_all_compliance': 'view_all_compliance',
                            'compliance.compliance_performance_analytics': 'compliance_performance_analytics',
                            # Policy permissions
                            'policy.create_policy': 'create_policy',
                            'policy.edit_policy': 'edit_policy',
                            'policy.approve_policy': 'approve_policy',
                            'policy.create_framework': 'create_framework',
                            'policy.approve_framework': 'approve_framework',
                            'policy.view_all_policy': 'view_all_policy',
                            'policy.policy_performance_analytics': 'policy_performance_analytics',
                            # Audit permissions
                            'audit.assign_audit': 'assign_audit',
                            'audit.conduct_audit': 'conduct_audit',
                            'audit.review_audit': 'review_audit',
                            'audit.view_audit_reports': 'view_audit_reports',
                            'audit.audit_performance_analytics': 'audit_performance_analytics',
                            # Risk permissions
                            'risk.create_risk': 'create_risk',
                            'risk.edit_risk': 'edit_risk',
                            'risk.approve_risk': 'approve_risk',
                            'risk.assign_risk': 'assign_risk',
                            'risk.evaluate_assigned_risk': 'evaluate_assigned_risk',
                            'risk.view_all_risk': 'view_all_risk',
                            'risk.risk_performance_analytics': 'risk_performance_analytics',
                            # Incident permissions
                            'incident.create_incident': 'create_incident',
                            'incident.edit_incident': 'edit_incident',
                            'incident.assign_incident': 'assign_incident',
                            'incident.evaluate_assigned_incident': 'evaluate_assigned_incident',
                            'incident.escalate_to_risk': 'escalate_to_risk',
                            'incident.view_all_incident': 'view_all_incident',
                            'incident.incident_performance_analytics': 'incident_performance_analytics',
                            # Event permissions
                            'event.create_event': 'create_event',
                            'event.edit_event': 'edit_event',
                            'event.approve_event': 'approve_event',
                            'event.reject_event': 'reject_event',
                            'event.archive_event': 'archive_event',
                            'event.view_all_event': 'view_all_event',
                            'event.view_module_event': 'view_module_event',
                            'event.event_performance_analytics': 'event_performance_analytics'
                        }
                        
                        # Get or create RBAC entry - use requested_role if provided, otherwise use default role
                        default_role = requested_role if requested_role else 'End User'
                        rbac_entry = RBAC.objects.filter(user=user, is_active='Y').first()
                        
                        if not rbac_entry:
                            # Create new RBAC entry
                            rbac_entry = RBAC.objects.create(
                                user=user,
                                username=user.UserName,
                                role=default_role,
                                is_active='Y',
                                FrameworkId=framework
                            )
                            logger.info(f"Created new RBAC entry for user {request_user_id} with role {default_role}")
                        else:
                            # Update role if requested_role is provided
                            if requested_role:
                                rbac_entry.role = requested_role
                        
                        # Update permission if required_permission is provided
                        if required_permission and required_permission in permission_field_map:
                            permission_field = permission_field_map[required_permission]
                            if hasattr(rbac_entry, permission_field):
                                setattr(rbac_entry, permission_field, True)
                                logger.info(f"Granted permission {required_permission} ({permission_field}) to user {request_user_id}")
                                audit_trail['rbac_permission_granted'] = required_permission
                                audit_trail['rbac_permission_field'] = permission_field
                            else:
                                logger.warning(f"Permission field {permission_field} not found in RBAC model for permission {required_permission}")
                                audit_trail['rbac_permission_error'] = f"Permission field {permission_field} not found"
                        elif required_permission:
                            logger.warning(f"Unknown permission format: {required_permission}")
                            audit_trail['rbac_permission_error'] = f"Unknown permission format: {required_permission}"
                        
                        # Save RBAC entry
                        rbac_entry.save()
                        
                        audit_trail['rbac_updated'] = True
                        audit_trail['rbac_role'] = rbac_entry.role
                        audit_trail['rbac_updated_at'] = updated_at.isoformat()
                        logger.info(f"Updated RBAC entry for user {request_user_id}")
                        
                except Exception as e:
                    logger.error(f"Error updating RBAC for access request {request_id}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    audit_trail['rbac_update_error'] = str(e)
            
            # Apply changes if approved (for RECTIFICATION type requests)
            elif new_status_upper == 'APPROVED' and apply_changes and audit_trail.get('changes'):
                try:
                    changes = audit_trail.get('changes', {})
                    info_type = audit_trail.get('info_type', 'personal')
                    
                    if info_type == 'personal':
                        # Update personal information
                        user = Users.objects.get(UserId=request_user_id)
                        if 'firstName' in changes:
                            user.FirstName = changes['firstName']['new']
                        if 'lastName' in changes:
                            user.LastName = changes['lastName']['new']
                        if 'email' in changes:
                            user.Email = changes['email']['new']
                        if 'phone' in changes:
                            # Note: Phone might be in a different table, adjust as needed
                            pass
                        user.save()
                        logger.info(f"Applied personal information changes for user {request_user_id}")
                    
                    elif info_type == 'business':
                        # Business information changes would need to update department/business unit tables
                        # This is more complex and may require additional logic
                        logger.info(f"Business information changes requested for user {request_user_id}")
                    
                    # Mark changes as applied in audit trail
                    audit_trail['changes_applied'] = True
                    audit_trail['changes_applied_at'] = updated_at.isoformat()
                    audit_trail['changes_applied_by'] = user_id
                    
                except Exception as e:
                    logger.error(f"Error applying changes: {str(e)}")
                    return Response(
                        {'status': 'error', 'message': f'Failed to apply changes: {str(e)}'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            # Add status change to audit trail
            if 'status_changes' not in audit_trail:
                audit_trail['status_changes'] = []
            
            audit_trail['status_changes'].append({
                'from_status': current_status,
                'to_status': new_status_upper,
                'changed_by': user_id,
                'changed_at': updated_at.isoformat(),
                'changes_applied': apply_changes if new_status_upper == 'APPROVED' else False
            })
            
            # Update the request - set approved_by if status is APPROVED
            # Also update verification_status to VERIFIED when approved or rejected
            # Ensure user_id is an integer for database storage (already converted above)
            
            if new_status_upper == 'APPROVED':
                # Set approved_by to the logged-in user who is approving
                # Set verification_status to VERIFIED
                cursor.execute("""
                    UPDATE `DataSubjectRequest`
                    SET status = %s,
                        updated_at = %s,
                        audit_trail = %s,
                        approved_by = %s,
                        verification_status = %s
                    WHERE id = %s
                """, [new_status_upper, updated_at, json.dumps(audit_trail), user_id_int, 'VERIFIED', request_id])
                logger.info(f"Request {request_id} approved by user {user_id_int}. approved_by column set to {user_id_int}, verification_status set to VERIFIED")
            elif new_status_upper == 'REJECTED':
                # For REJECTED, set verification_status to VERIFIED but don't set approved_by
                cursor.execute("""
                    UPDATE `DataSubjectRequest`
                    SET status = %s,
                        updated_at = %s,
                        audit_trail = %s,
                        verification_status = %s
                    WHERE id = %s
                """, [new_status_upper, updated_at, json.dumps(audit_trail), 'VERIFIED', request_id])
                logger.info(f"Request {request_id} rejected by user {user_id_int}. verification_status set to VERIFIED")
            else:
                # For other statuses, don't change verification_status or approved_by
                cursor.execute("""
                    UPDATE `DataSubjectRequest`
                    SET status = %s,
                        updated_at = %s,
                        audit_trail = %s
                    WHERE id = %s
                """, [new_status_upper, updated_at, json.dumps(audit_trail), request_id])
                logger.info(f"Request {request_id} status updated from {current_status} to {new_status_upper} by user {user_id_int}")
            
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
        logger.error(f"Error updating data subject request status: {str(e)}")
        return Response(
            {'status': 'error', 'message': f'Failed to update request: {str(e)}'}, 
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
        # Get user making the request
        requesting_user_id = RBACUtils.get_user_id_from_request(request)
        if not requesting_user_id:
            return Response(
                {'status': 'error', 'message': 'User not authenticated'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is an admin
        admin_user_ids = [1, 2, 3, 4]
        try:
            requesting_user_id_int = int(requesting_user_id)
            is_admin = requesting_user_id_int in admin_user_ids
        except (ValueError, TypeError):
            is_admin = False
        
        # This works around Django's table name lowercasing issue
        with connection.cursor() as cursor:
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
                    FROM `AccessRequest` ar
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
                    FROM `AccessRequest` ar
                    LEFT JOIN `users` approver ON ar.approved_by = approver.UserId
                    WHERE ar.user_id = %s
                    ORDER BY ar.created_at DESC
                """, [user_id])
            
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            
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
            
            return Response({
                'status': 'success',
                'data': requests
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error fetching access requests: {str(e)}")
        return Response(
            {'status': 'error', 'message': f'Failed to fetch access requests: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@csrf_exempt
@authentication_classes([])
@permission_classes([AllowAny])
def create_access_request(request):
    """
    Create a new access request
    """
    try:
        # Get user ID from request
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response(
                {'status': 'error', 'message': 'User not authenticated'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get request data
        requested_url = request.data.get('requested_url', '')
        requested_feature = request.data.get('requested_feature', '')
        required_permission = request.data.get('required_permission', '')
        requested_role = request.data.get('requested_role', '')
        message = request.data.get('message', '')
        
        # Log the received data for debugging
        logger.info(f"Creating access request - URL: {requested_url}, Feature: {requested_feature}, Permission: {required_permission}, Role: {requested_role}")
        
        # Create audit trail
        audit_trail = {
            'requested_url': requested_url,
            'requested_feature': requested_feature,
            'required_permission': required_permission,
            'requested_role': requested_role,
            'message': message,
            'requested_by': user_id
        }
        
        # Create the access request using raw SQL
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO `AccessRequest` 
                (user_id, requested_url, requested_feature, required_permission, requested_role, status, message, audit_trail, approved_by, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                user_id,
                requested_url or None,  # Store None instead of empty string
                requested_feature or None,
                required_permission or None,  # Store None instead of empty string
                requested_role or None,
                'REQUESTED',
                message or None,
                json.dumps(audit_trail),
                None,  # approved_by is NULL initially
                timezone.now(),
                timezone.now()
            ])
            
            request_id = cursor.lastrowid
        
        logger.info(f"Access request {request_id} created by user {user_id} - URL: {requested_url}, Permission: {required_permission}")
        
        return Response({
            'status': 'success',
            'message': 'Access request created successfully',
            'data': {
                'id': request_id,
                'status': 'REQUESTED',
                'created_at': timezone.now().isoformat()
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating access request: {str(e)}")
        return Response(
            {'status': 'error', 'message': f'Failed to create request: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['PUT'])
@authentication_classes([])
@permission_classes([AllowAny])
def update_access_request_status(request, request_id):
    """
    Update the status of an access request (Approve/Reject)
    Only GRC Administrators can approve/reject requests
    When approved, updates RBAC table with requested role
    """
    try:
            # Get the request
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, status, requested_role, required_permission, audit_trail
                FROM `AccessRequest`
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
            
            # Get the user making the update from request
            user_id = RBACUtils.get_user_id_from_request(request)
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
            
            # If approved, update RBAC table
            # If rejected, do NOT update RBAC table (leave permissions unchanged)
            if new_status_upper == 'APPROVED':
                try:
                    logger.info(f"Processing RBAC update for approved access request {request_id}, user {request_user_id}, permission: {required_permission}")
                    
                    # Get user
                    user = Users.objects.get(UserId=request_user_id)
                    
                    # Get or create framework - use user's framework or first available
                    framework = getattr(user, 'FrameworkId', None)
                    if not framework:
                        framework = Framework.objects.filter(Status='Approved', ActiveInactive='Active').first()
                    
                    if not framework:
                        logger.warning(f"No framework found for access request {request_id}")
                        audit_trail['rbac_update_error'] = 'No framework found'
                    else:
                        # Map permission string (module.permission) to RBAC field name
                        # This mapping covers ALL modules and ALL permissions in the system
                        permission_field_map = {
                            # Compliance permissions
                            'compliance.create_compliance': 'create_compliance',
                            'compliance.edit_compliance': 'edit_compliance',
                            'compliance.approve_compliance': 'approve_compliance',
                            'compliance.view_all_compliance': 'view_all_compliance',
                            'compliance.compliance_performance_analytics': 'compliance_performance_analytics',
                            # Policy permissions
                            'policy.create_policy': 'create_policy',
                            'policy.edit_policy': 'edit_policy',
                            'policy.approve_policy': 'approve_policy',
                            'policy.create_framework': 'create_framework',
                            'policy.approve_framework': 'approve_framework',
                            'policy.view_all_policy': 'view_all_policy',
                            'policy.policy_performance_analytics': 'policy_performance_analytics',
                            # Audit permissions
                            'audit.assign_audit': 'assign_audit',
                            'audit.conduct_audit': 'conduct_audit',
                            'audit.review_audit': 'review_audit',
                            'audit.view_audit_reports': 'view_audit_reports',
                            'audit.audit_performance_analytics': 'audit_performance_analytics',
                            # Risk permissions
                            'risk.create_risk': 'create_risk',
                            'risk.edit_risk': 'edit_risk',
                            'risk.approve_risk': 'approve_risk',
                            'risk.assign_risk': 'assign_risk',
                            'risk.evaluate_assigned_risk': 'evaluate_assigned_risk',
                            'risk.view_all_risk': 'view_all_risk',
                            'risk.risk_performance_analytics': 'risk_performance_analytics',
                            # Incident permissions
                            'incident.create_incident': 'create_incident',
                            'incident.edit_incident': 'edit_incident',
                            'incident.assign_incident': 'assign_incident',
                            'incident.evaluate_assigned_incident': 'evaluate_assigned_incident',
                            'incident.escalate_to_risk': 'escalate_to_risk',
                            'incident.view_all_incident': 'view_all_incident',
                            'incident.incident_performance_analytics': 'incident_performance_analytics',
                            # Event permissions
                            'event.create_event': 'create_event',
                            'event.edit_event': 'edit_event',
                            'event.approve_event': 'approve_event',
                            'event.reject_event': 'reject_event',
                            'event.archive_event': 'archive_event',
                            'event.view_all_event': 'view_all_event',
                            'event.view_module_event': 'view_module_event',
                            'event.event_performance_analytics': 'event_performance_analytics'
                        }
                        
                        # Get or create RBAC entry - use requested_role if provided, otherwise use default role
                        default_role = requested_role if requested_role else 'End User'
                        rbac_entry = RBAC.objects.filter(user=user, is_active='Y').first()
                        
                        if not rbac_entry:
                            # Create new RBAC entry
                            rbac_entry = RBAC.objects.create(
                                user=user,
                                username=user.UserName,
                                role=default_role,
                                is_active='Y',
                                FrameworkId=framework
                            )
                            logger.info(f"Created new RBAC entry for user {request_user_id} with role {default_role}")
                        else:
                            # Update role if requested_role is provided
                            if requested_role:
                                rbac_entry.role = requested_role
                        
                        # Update permission if required_permission is provided
                        if required_permission and required_permission in permission_field_map:
                            permission_field = permission_field_map[required_permission]
                            if hasattr(rbac_entry, permission_field):
                                setattr(rbac_entry, permission_field, True)
                                logger.info(f"Granted permission {required_permission} ({permission_field}) to user {request_user_id}")
                                audit_trail['rbac_permission_granted'] = required_permission
                                audit_trail['rbac_permission_field'] = permission_field
                            else:
                                logger.warning(f"Permission field {permission_field} not found in RBAC model for permission {required_permission}")
                                audit_trail['rbac_permission_error'] = f"Permission field {permission_field} not found"
                        elif required_permission:
                            logger.warning(f"Unknown permission format: {required_permission}")
                            audit_trail['rbac_permission_error'] = f"Unknown permission format: {required_permission}"
                        
                        # Save RBAC entry
                        rbac_entry.save()
                        
                        audit_trail['rbac_updated'] = True
                        audit_trail['rbac_role'] = rbac_entry.role
                        audit_trail['rbac_updated_at'] = updated_at.isoformat()
                        logger.info(f"Updated RBAC entry for user {request_user_id}")
                        
                except Exception as e:
                    logger.error(f"Error updating RBAC for access request {request_id}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    audit_trail['rbac_update_error'] = str(e)
            elif new_status_upper == 'REJECTED':
                # Explicitly log that RBAC is NOT being updated for rejected requests
                logger.info(f"Access request {request_id} rejected - RBAC table will NOT be updated (permissions remain unchanged)")
                audit_trail['rbac_update_skipped'] = True
                audit_trail['rbac_update_reason'] = 'Request rejected - permissions unchanged'
            
            # Update the request status in AccessRequest table
            if new_status_upper == 'APPROVED':
                cursor.execute("""
                    UPDATE `AccessRequest`
                    SET status = %s,
                        updated_at = %s,
                        audit_trail = %s,
                        approved_by = %s
                    WHERE id = %s
                """, [new_status_upper, updated_at, json.dumps(audit_trail), user_id_int, request_id])
            else:
                cursor.execute("""
                    UPDATE `AccessRequest`
                    SET status = %s,
                        updated_at = %s,
                        audit_trail = %s
                    WHERE id = %s
                """, [new_status_upper, updated_at, json.dumps(audit_trail), request_id])
            
            logger.info(f"Access request {request_id} {new_status.lower()} by user {user_id_int}")
            
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
        logger.error(f"Error updating access request status: {str(e)}")
        return Response(
            {'status': 'error', 'message': f'Failed to update request: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )