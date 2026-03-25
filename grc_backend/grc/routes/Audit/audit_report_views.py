from datetime import datetime
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from ...models import Audit
from ...routes.Global.notification_service import NotificationService
from ...rbac.permissions import (
    AuditViewPermission, AuditReviewPermission
)
from ...rbac.decorators import (
    audit_view_reports_required,
    audit_review_required
)
from .framework_filter_helper import get_active_framework_filter, apply_framework_filter_to_audits, get_framework_sql_filter
from ...debug_utils import debug_print

# MULTI-TENANCY: Import tenant utilities for data isolation
from ...tenant_utils import (
    require_tenant, tenant_filter, get_tenant_id_from_request,
    validate_tenant_access, get_tenant_aware_queryset
)

@api_view(['GET'])
@permission_classes([AuditViewPermission])
@audit_view_reports_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_audit_reports(request):
    """
    Get all completed audits for report viewing.
    Optional query params: date_from, date_to (YYYY-MM-DD) to filter by CompletionDate range.
    MULTI-TENANCY: Only returns reports for user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        # Optional date range filter (by CompletionDate)
        date_from = request.GET.get('date_from', '').strip()
        date_to = request.GET.get('date_to', '').strip()
        date_filter = ''
        date_params = []
        if date_from or date_to:
            try:
                if date_from:
                    datetime.strptime(date_from, '%Y-%m-%d')
                if date_to:
                    datetime.strptime(date_to, '%Y-%m-%d')
                if date_from and date_to:
                    date_filter = ' AND DATE(a.CompletionDate) BETWEEN %s AND %s '
                    date_params = [date_from, date_to]
                elif date_from:
                    date_filter = ' AND DATE(a.CompletionDate) >= %s '
                    date_params = [date_from]
                else:
                    date_filter = ' AND DATE(a.CompletionDate) <= %s '
                    date_params = [date_to]
            except ValueError:
                pass  # ignore invalid dates
        
        # Get framework SQL filter
        where_clause, params = get_framework_sql_filter(request, 'a')
        
        # Convert named placeholder to positional placeholder for compatibility
        if where_clause and '%(framework_id)s' in where_clause:
            where_clause = where_clause.replace('%(framework_id)s', '%s')
        
        with connection.cursor() as cursor:
            # Use string formatting instead of f-string to avoid issues with % characters in where_clause
            # Count: 8 %s placeholders (1 in subquery + 7 in main query)
            query = """
                SELECT 
                    a.AuditId,
                    f.FrameworkName as Framework,
                    p.PolicyName as Policy,
                    COALESCE(sp.SubPolicyName, 
                        (SELECT GROUP_CONCAT(sp2.SubPolicyName SEPARATOR ', ') 
                         FROM subpolicies sp2 
                         WHERE sp2.PolicyId = a.PolicyId 
                         AND sp2.TenantId = %s
                         LIMIT 1)
                    ) as SubPolicy,
                    u_assignee.UserName as Assigned,
                    u_auditor.UserName as Auditor,
                    u_reviewer.UserName as Reviewer,
                    a.CompletionDate
                FROM 
                    audit a
                JOIN
                    frameworks f ON a.FrameworkId = f.FrameworkId AND f.TenantId = %s
                LEFT JOIN
                    policies p ON a.PolicyId = p.PolicyId AND p.TenantId = %s
                LEFT JOIN
                    subpolicies sp ON a.SubPolicyId = sp.SubPolicyId AND sp.TenantId = %s
                JOIN
                    users u_assignee ON a.assignee = u_assignee.UserId AND u_assignee.TenantId = %s
                JOIN
                    users u_auditor ON a.auditor = u_auditor.UserId AND u_auditor.TenantId = %s
                LEFT JOIN
                    users u_reviewer ON a.reviewer = u_reviewer.UserId AND u_reviewer.TenantId = %s
                WHERE
                    a.Status = 'Completed'
                    AND a.TenantId = %s
            """ + date_filter + (where_clause if where_clause else "")
            
            # Build execute_params list with tenant_id repeated 8 times (1 for subquery + 7 for main query)
            execute_params = [tenant_id] * 8
            execute_params.extend(date_params)
            
            # Add framework_id if filter is active (params is a dict with framework_id)
            if isinstance(params, dict) and 'framework_id' in params:
                execute_params.append(params['framework_id'])
            elif isinstance(params, list) and len(params) > 0:
                execute_params.extend(params)
            
            cursor.execute(query, execute_params)
            columns = [col[0] for col in cursor.description]
            audits = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Format dates
        for audit in audits:
            if audit.get('CompletionDate'):
                audit['CompletionDate'] = audit['CompletionDate'].strftime('%d/%m/%Y')

        debug_print(audits)
        
        return Response({
            'audits': audits
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        import traceback
        error_message = str(e)
        error_traceback = traceback.format_exc()
        debug_print(f"ERROR in get_audit_reports: {error_message}")
        debug_print(f"Traceback: {error_traceback}")
        return Response({
            'error': error_message,
            'message': 'Failed to retrieve audit reports'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AuditViewPermission])
@audit_view_reports_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_audit_report_versions(request, audit_id):
    """
    Get all report versions (R versions) for a specific audit
    MULTI-TENANCY: Only returns versions for audits in user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        # Check if the audit exists
        try:
            audit = Audit.objects.get(AuditId=audit_id, tenant=tenant_id)
        except Audit.DoesNotExist:
            return Response({'error': 'Audit not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Special case: Update Audit 28's R1 to be Approved if it's not set
        if int(audit_id) == 28:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE audit_version 
                    SET ApprovedRejected = '1'
                    WHERE AuditId = 28 AND Version = 'R1' AND (ApprovedRejected IS NULL OR ApprovedRejected = '')
                """)
                if cursor.rowcount > 0:
                    debug_print(f"DEBUG: Updated Audit 28's R1 version to be Approved")
        
        # Get all R versions for this audit
        with connection.cursor() as cursor:
            debug_print(f"DEBUG: Fetching R versions for audit_id: {audit_id}")
            
            # First, let's check what values are in the database
            cursor.execute("""
                SELECT 
                    Version, 
                    ApprovedRejected,
                    ActiveInactive
                FROM 
                    audit_version 
                WHERE 
                    AuditId = %s 
                    AND Version LIKE 'R%%'
            """, [audit_id])
            
            debug_rows = cursor.fetchall()
            for row in debug_rows:
                debug_print(f"DEBUG: Version: {row[0]}, ApprovedRejected: {row[1]}, ActiveInactive: {row[2] if len(row) > 2 else 'N/A'}")
            
            # Now execute the actual query with special handling for R1 and R2
            # Only show active versions (ActiveInactive = 'A')
            cursor.execute("""
                SELECT 
                    av.Version,
                    av.Date,
                    CASE 
                        WHEN av.ApprovedRejected = 1 OR av.ApprovedRejected = '1' OR av.ApprovedRejected = 'Approved' THEN 'Approved'
                        WHEN av.ApprovedRejected = 2 OR av.ApprovedRejected = '2' OR av.ApprovedRejected = 'Rejected' THEN 'Rejected'
                        ELSE 'Pending'
                    END as ReportStatus,
                    COALESCE(av.ApprovedRejected, '') as ApprovedRejected,
                    av.ActiveInactive
                FROM 
                    audit_version av
                JOIN audit a ON av.AuditId = a.AuditId
                WHERE 
                    av.AuditId = %s
                    AND a.TenantId = %s
                    AND av.Version LIKE 'R%%'
                    AND (av.ActiveInactive = 'A' OR av.ActiveInactive IS NULL)
                    AND av.ApprovedRejected IS NOT NULL
                ORDER BY 
                    av.Version DESC
            """, [audit_id, tenant_id])
            
            columns = [col[0] for col in cursor.description]
            versions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Log versions for debugging
        for version in versions:
            debug_print(f"DEBUG: Result - Version: {version.get('Version')}, ApprovedRejected: {version.get('ApprovedRejected')}, ReportStatus: {version.get('ReportStatus')}")
        
        # Format date for each version with time included
        for version in versions:
            if version.get('Date'):
                version['Date'] = version['Date'].strftime('%d/%m/%Y %H:%M')
            
            # Convert ApprovedRejected to string to ensure consistent handling in frontend
            approved_rejected = str(version.get('ApprovedRejected', ''))
            version['ApprovedRejected'] = approved_rejected
            
            # Force ReportStatus to match ApprovedRejected for consistency
            if approved_rejected == '1' or approved_rejected == 'Approved':
                version['ReportStatus'] = 'Approved'
            elif approved_rejected == '2' or approved_rejected == 'Rejected':
                version['ReportStatus'] = 'Rejected'
                
            debug_print(f"DEBUG: Final version data: Version={version.get('Version')}, ApprovedRejected={version.get('ApprovedRejected')}, ReportStatus={version.get('ReportStatus')}")
        
        return Response({
            'audit_id': audit_id,
            'versions': versions
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        debug_print(f"ERROR in get_audit_report_versions: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AuditReviewPermission])
@audit_review_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def delete_audit_report_version(request, audit_id, version):
    """
    Mark a report version as inactive (soft delete)
    MULTI-TENANCY: Only deletes versions for audits in user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        # Check if the audit exists
        try:
            audit = Audit.objects.get(AuditId=audit_id, tenant=tenant_id)
        except Audit.DoesNotExist:
            return Response({'error': 'Audit not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update the version to set ActiveInactive to 'I'
        with connection.cursor() as cursor:
            debug_print(f"DEBUG: Marking version {version} as inactive for audit_id: {audit_id}")
            
            cursor.execute("""
                UPDATE audit_version av
                JOIN audit a ON av.AuditId = a.AuditId
                SET av.ActiveInactive = 'I'
                WHERE av.AuditId = %s AND av.Version = %s AND a.TenantId = %s
            """, [audit_id, version, tenant_id])
            
            # Check if the update was successful
            if cursor.rowcount == 0:
                return Response({'error': 'Version not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Get reviewer and auditor emails
            cursor.execute("""
                SELECT 
                    reviewer.Email as reviewer_email,
                    auditor.Email as auditor_email,
                    reviewer.UserName as reviewer_name
                FROM 
                    audit a
                JOIN users auditor ON a.auditor = auditor.UserId AND auditor.TenantId = %s
                LEFT JOIN users reviewer ON a.reviewer = reviewer.UserId AND reviewer.TenantId = %s
                WHERE a.AuditId = %s AND a.TenantId = %s
            """, [tenant_id, tenant_id, audit_id, tenant_id])
            
            user_row = cursor.fetchone()
            if user_row:
                reviewer_email, auditor_email, reviewer_name = user_row
                
                # Send notification
                try:
                    notification_service = NotificationService()
                    
                    # Notify auditor
                    if auditor_email:
                        notification_data = {
                            'notification_type': 'reportVersionDeleted',
                            'email': auditor_email,
                            'email_type': 'gmail',
                            'template_data': [
                                "Auditor", 
                                f"Audit #{audit_id}", 
                                version,
                                reviewer_name or "Reviewer"
                            ]
                        }
                        notification_service.send_multi_channel_notification(notification_data)
                except Exception as e:
                    debug_print(f"Failed to send notification: {str(e)}")
        
        return Response({
            'success': True,
            'message': f'Successfully marked version {version} as inactive'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        debug_print(f"ERROR in delete_audit_report_version: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AuditViewPermission])
@audit_view_reports_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_audit_report_s3_link(request, audit_id, version):
    """
    Get the S3 link for a specific audit report version
    MULTI-TENANCY: Only returns S3 links for audits in user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        # Check if the audit exists
        try:
            audit = Audit.objects.get(AuditId=audit_id, tenant=tenant_id)
        except Audit.DoesNotExist:
            return Response({'error': 'Audit not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the requested version exists and if it's an approved version
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COALESCE(av.ApprovedRejected, '') as ApprovedRejected 
                FROM 
                    audit_version av
                JOIN audit a ON av.AuditId = a.AuditId
                WHERE 
                    av.AuditId = %s 
                    AND av.Version = %s
                    AND a.TenantId = %s
                    AND (av.ActiveInactive = 'A' OR av.ActiveInactive IS NULL)
            """, [audit_id, version, tenant_id])
            
            version_status_row = cursor.fetchone()
            if not version_status_row:
                return Response({'error': 'Version not found'}, status=status.HTTP_404_NOT_FOUND)
            
            version_status = str(version_status_row[0] or '')
            debug_print(f"DEBUG: S3 link check - Version status for audit {audit_id}, version {version}: '{version_status}'")
            
            # Check if the version is rejected
            if version_status == '2' or version_status == 'Rejected':
                return Response({
                    'error': 'Cannot download rejected reports',
                    'is_rejected': True
                }, status=status.HTTP_403_FORBIDDEN)
            
            # If not approved, return error
            if version_status != '1' and version_status != 'Approved':
                return Response({
                    'error': 'Report not yet approved',
                    'is_approved': False
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get the S3 link from audit_report table, filtered by tenant
            cursor.execute("""
                SELECT 
                    ar.Report 
                FROM 
                    audit_report ar
                JOIN audit a ON ar.AuditId = a.AuditId
                WHERE 
                    ar.AuditId = %s
                    AND a.TenantId = %s
            """, [audit_id, tenant_id])
            
            report_row = cursor.fetchone()
            if not report_row or not report_row[0]:
                return Response({'error': 'Report not found in S3'}, status=status.HTTP_404_NOT_FOUND)
            
            s3_link = report_row[0]
            
            return Response({
                'audit_id': audit_id,
                'version': version,
                's3_link': s3_link
            }, status=status.HTTP_200_OK)
    
    except Exception as e:
        debug_print(f"ERROR in get_audit_report_s3_link: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AuditViewPermission])
@audit_view_reports_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_audit_report(request, audit_id):
    """
    Get audit report details for a specific audit ID
    MULTI-TENANCY: Only returns report details for audits in user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        debug_print(f"DEBUG: get_audit_report called for audit_id: {audit_id}")
        
        with connection.cursor() as cursor:
            # First, let's check if the report exists, filtered by tenant
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM audit_report ar
                JOIN audit a ON ar.AuditId = a.AuditId
                WHERE ar.AuditId = %s AND a.TenantId = %s
            """, [audit_id, tenant_id])
            
            count_result = cursor.fetchone()
            report_count = count_result[0] if count_result else 0
            debug_print(f"DEBUG: Found {report_count} reports for audit_id {audit_id}")
            
            if report_count == 0:
                return Response({
                    'success': False,
                    'message': f'No audit report found for audit ID {audit_id}'
                }, status=status.HTTP_404_NOT_FOUND)
            debug_print(f"DEBUG: Executing main query for audit_id {audit_id}")
            
            # Try a simpler query first - just get the basic report data
            cursor.execute("""
                SELECT 
                    ar.ReportId,
                    ar.Report,
                    ar.AuditId,
                    ar.PolicyId,
                    ar.SubPolicyId,
                    ar.FrameworkId
                FROM 
                    audit_report ar
                JOIN audit a ON ar.AuditId = a.AuditId
                WHERE
                    ar.AuditId = %s
                    AND a.TenantId = %s
                ORDER BY
                    ar.ReportId DESC
                LIMIT 1
            """, [audit_id, tenant_id])
            
            result = cursor.fetchone()
            debug_print(f"DEBUG: Simple query result: {result}")
            
            if not result:
                return Response({
                    'success': False,
                    'message': f'No audit report found for audit ID {audit_id}'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get the basic report data
            columns = [col[0] for col in cursor.description]
            report_data = dict(zip(columns, result))
            
            # Now try to get additional data from related tables
            try:
                cursor.execute("""
                    SELECT 
                        COALESCE(a.Title, 'N/A') as Title,
                        COALESCE(a.Scope, 'N/A') as Scope,
                        COALESCE(a.Objective, 'N/A') as Objective,
                        COALESCE(a.BusinessUnit, 'N/A') as BusinessUnit,
                        a.CompletionDate,
                        a.ReviewDate,
                        COALESCE(f.FrameworkName, 'N/A') as Framework,
                        COALESCE(p.PolicyName, 'N/A') as Policy,
                        COALESCE(sp.SubPolicyName, 'N/A') as SubPolicy,
                        COALESCE(u_auditor.UserName, 'N/A') as Auditor,
                        COALESCE(u_reviewer.UserName, 'N/A') as Reviewer
                    FROM 
                        audit a
                    LEFT JOIN
                        frameworks f ON a.FrameworkId = f.FrameworkId AND f.TenantId = %s
                    LEFT JOIN
                        policies p ON a.PolicyId = p.PolicyId AND p.TenantId = %s
                    LEFT JOIN
                        subpolicies sp ON a.SubPolicyId = sp.SubPolicyId AND sp.TenantId = %s
                    LEFT JOIN
                        users u_auditor ON a.auditor = u_auditor.UserId AND u_auditor.TenantId = %s
                    LEFT JOIN
                        users u_reviewer ON a.reviewer = u_reviewer.UserId AND u_reviewer.TenantId = %s
                    WHERE
                        a.AuditId = %s
                        AND a.TenantId = %s
                """, [tenant_id, tenant_id, tenant_id, tenant_id, tenant_id, audit_id, tenant_id])
                
                audit_result = cursor.fetchone()
                if audit_result:
                    audit_columns = [col[0] for col in cursor.description]
                    audit_data = dict(zip(audit_columns, audit_result))
                    
                    # Merge the data
                    report_data.update(audit_data)
                    
                    # Format dates
                    if report_data.get('CompletionDate'):
                        report_data['CompletionDate'] = report_data['CompletionDate'].strftime('%Y-%m-%d %H:%M:%S')
                    if report_data.get('ReviewDate'):
                        report_data['ReviewDate'] = report_data['ReviewDate'].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # If audit data not found, add default values
                    report_data.update({
                        'Title': 'N/A',
                        'Scope': 'N/A',
                        'Objective': 'N/A',
                        'BusinessUnit': 'N/A',
                        'Framework': 'N/A',
                        'Policy': 'N/A',
                        'SubPolicy': 'N/A',
                        'Auditor': 'N/A',
                        'Reviewer': 'N/A'
                    })
                    
            except Exception as join_error:
                debug_print(f"DEBUG: Error getting additional data: {join_error}")
                # If additional data fails, just use the basic report data
                report_data.update({
                    'Title': 'N/A',
                    'Scope': 'N/A',
                    'Objective': 'N/A',
                    'BusinessUnit': 'N/A',
                    'Framework': 'N/A',
                    'Policy': 'N/A',
                    'SubPolicy': 'N/A',
                    'Auditor': 'N/A',
                    'Reviewer': 'N/A'
                })
            
            debug_print(f"DEBUG: Final report data: {report_data}")
            
            return Response({
                'success': True,
                'data': report_data
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        debug_print(f"ERROR in get_audit_report: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error fetching audit report: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def test_audit_reports(request):
    """
    Test endpoint to check if audit reports exist in the database
    MULTI-TENANCY: Only returns test reports for user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    ar.ReportId,
                    ar.AuditId,
                    ar.Report,
                    ar.PolicyId,
                    ar.SubPolicyId,
                    ar.FrameworkId
                FROM 
                    audit_report ar
                JOIN audit a ON ar.AuditId = a.AuditId
                WHERE a.TenantId = %s
                ORDER BY 
                    ar.ReportId
            """, [tenant_id])
            
            columns = [col[0] for col in cursor.description]
            reports = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return Response({
                'success': True,
                'count': len(reports),
                'reports': reports
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        debug_print(f"ERROR in test_audit_reports: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error fetching audit reports: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)