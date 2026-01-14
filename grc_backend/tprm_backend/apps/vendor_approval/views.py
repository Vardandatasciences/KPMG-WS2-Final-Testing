"""

Vendor Approval Views - API endpoints for approval workflow management

"""



import uuid

import json

from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt

from django.views.decorators.http import require_http_methods

from django.utils.decorators import method_decorator

from django.db import connection

from django.db import connections

from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes, authentication_classes

from rest_framework.permissions import AllowAny

from rest_framework.response import Response

from rest_framework import status

from .models import Users, ApprovalWorkflows, ApprovalRequests, ApprovalStages, ApprovalRequestVersions, TempVendor, ExternalScreeningResults, ScreeningMatches

from tprm_backend.risk_analysis_vendor.models import Risk

from tprm_backend.apps.vendor_questionnaire.models import QuestionnaireAssignments, QuestionnaireResponseSubmissions, QuestionnaireQuestions

from django.db import transaction

# RBAC imports
from tprm_backend.rbac.tprm_decorators import rbac_vendor_required
from tprm_backend.apps.vendor_core.vendor_authentication import JWTAuthentication, SimpleAuthenticatedPermission

# MULTI-TENANCY: Import tenant utilities for filtering
from tprm_backend.core.tenant_utils import (
    get_tenant_id_from_request,
    filter_queryset_by_tenant,
    get_tenant_aware_queryset,
    require_tenant,
    tenant_filter
)



def compute_exponent_normalized_weights(raw_values, target_sum=10.0, max_iterations=40):
    """
    Compute normalized weights from raw influence values using:
        a^x + b^x + c^x + ... = target_sum

    Returns a list of weights that:
      - are all positive (when there is at least one positive raw value)
      - sum to 1.0
      - reflect the relative strengths of the raw values
    """
    try:
        # Filter and sanitize raw values
        values = []
        for v in raw_values or []:
            try:
                fv = float(v)
            except (TypeError, ValueError):
                fv = 0.0
            # Only keep strictly positive influences
            if fv > 0:
                values.append(fv)

        n = len(values)
        if n == 0:
            return []

        # Edge case: single reviewer → full weight
        if n == 1:
            return [1.0]

        # Binary search for exponent x in a reasonable range.
        # In most realistic cases, influences are between 1 and 100.
        # We search x in [0.01, 5.0], which is sufficient and numerically stable.
        lo, hi = 0.01, 5.0

        def sum_powers(x):
            total = 0.0
            for a in values:
                if a <= 0:
                    continue
                total += a ** x
            return total

        for _ in range(max_iterations):
            mid = (lo + hi) / 2.0
            total = sum_powers(mid)

            # If total is too large, decrease exponent; if too small, increase
            if total > target_sum:
                hi = mid
            else:
                lo = mid

        x = (lo + hi) / 2.0

        # Compute final weights; normalize to guarantee sum == 1
        powered = []
        for a in values:
            if a <= 0:
                powered.append(0.0)
            else:
                powered.append(a ** x)

        total_powered = sum(powered)
        if total_powered <= 0:
            # Fallback to equal weights if numerical issues occur
            equal_w = 1.0 / n
            return [equal_w for _ in range(n)]

        return [p / total_powered for p in powered]

    except Exception as e:
        # Never fail the overall flow due to weighting; fall back to equal weights
        try:
            n = len([v for v in (raw_values or []) if float(v) > 0])
        except Exception:
            n = len(raw_values) if raw_values is not None else 0
        if n <= 0:
            return []
        equal_w = 1.0 / n
        print(f"Warning - compute_exponent_normalized_weights fallback to equal weights: {str(e)}")
        return [equal_w for _ in range(n)]





def migrate_vendor_from_temp_to_main(temp_vendor_id, user_id=None):

    """

    Migrate vendor data from temp_vendor table to main vendor tables (vendors, vendor_contacts, vendor_documents)

    

    Args:
 
        temp_vendor_id (int): ID of the temp vendor to migrate

        user_id (int): ID of the user performing the migration (for created_by/updated_by fields)

    

    Returns:

        dict: Result with success status, vendor_id, and any error messages

    """

    try:

        with transaction.atomic():

            # Get the temp vendor data

            temp_vendor = TempVendor.objects.get(id=temp_vendor_id)

            

            # Check if vendor already exists in main table (by vendor_code)

            existing_vendor = None

            if temp_vendor.vendor_code:

                with connections['default'].cursor() as cursor:

                    cursor.execute("SELECT vendor_id FROM vendors WHERE vendor_code = %s", [temp_vendor.vendor_code])

                    existing_vendor = cursor.fetchone()

            

            if existing_vendor:

                return {

                    'success': False,

                    'error': f'Vendor with code {temp_vendor.vendor_code} already exists in main table',

                    'vendor_id': existing_vendor[0]

                }

            

            # Prepare vendor data for main table

            vendor_data = {

                'vendor_code': temp_vendor.vendor_code or f'TEMP_{temp_vendor.id}',

                'company_name': temp_vendor.company_name,

                'legal_name': temp_vendor.legal_name,

                'business_type': temp_vendor.business_type,

                'incorporation_date': temp_vendor.incorporation_date,

                'tax_id': temp_vendor.tax_id,

                'duns_number': temp_vendor.duns_number,

                'website': temp_vendor.website,

                'industry_sector': temp_vendor.industry_sector,

                'annual_revenue': temp_vendor.annual_revenue,

                'employee_count': temp_vendor.employee_count,

                'headquarters_address': temp_vendor.headquarters_address,

                'description': temp_vendor.description,

                'risk_level': temp_vendor.risk_level.upper() if temp_vendor.risk_level else 'LOW',

                'status': 'APPROVED',  # Set to APPROVED since this is called after final approval

                'lifecycle_stage': 'ONBOARDED',

                'onboarding_date': timezone.now().date(),

                'is_critical_vendor': 1 if temp_vendor.is_critical_vendor else 0,

                'has_data_access': 1 if temp_vendor.has_data_access else 0,

                'has_system_access': 1 if temp_vendor.has_system_access else 0,

                'created_by': user_id,

                'updated_by': user_id,

                'created_at': timezone.now(),

                'updated_at': timezone.now()

            }

            

            # Insert into main vendors table

            with connections['default'].cursor() as cursor:

                # Build the INSERT query dynamically

                columns = list(vendor_data.keys())

                placeholders = ['%s'] * len(columns)

                values = list(vendor_data.values())

                

                insert_query = f"""

                    INSERT INTO vendors ({', '.join(columns)})

                    VALUES ({', '.join(placeholders)})

                """

                

                cursor.execute(insert_query, values)

                new_vendor_id = cursor.lastrowid

                

                print(f"Successfully migrated vendor {temp_vendor.company_name} to main table with ID: {new_vendor_id}")

            

            # Migrate contacts if they exist

            contacts_migrated = 0

            if temp_vendor.contacts:

                try:

                    contacts_data = temp_vendor.contacts if isinstance(temp_vendor.contacts, list) else []

                    

                    for contact in contacts_data:

                        if contact and isinstance(contact, dict):

                            contact_data = {

                                'vendor_id': new_vendor_id,

                                'contact_type': contact.get('contact_type', 'PRIMARY'),

                                'first_name': contact.get('first_name', ''),

                                'last_name': contact.get('last_name', ''),

                                'email': contact.get('email', ''),

                                'phone': contact.get('phone', ''),

                                'mobile': contact.get('mobile', ''),

                                'designation': contact.get('designation', ''),

                                'department': contact.get('department', ''),

                                'is_primary': 1 if contact.get('is_primary', False) else 0,

                                'is_active': 1,

                                'created_at': timezone.now(),

                                'updated_at': timezone.now()

                            }

                            

                            # Insert contact

                            with connections['default'].cursor() as cursor:

                                contact_columns = list(contact_data.keys())

                                contact_placeholders = ['%s'] * len(contact_columns)

                                contact_values = list(contact_data.values())

                                

                                contact_insert_query = f"""

                                    INSERT INTO vendor_contacts ({', '.join(contact_columns)})

                                    VALUES ({', '.join(contact_placeholders)})

                                """

                                

                                cursor.execute(contact_insert_query, contact_values)

                                contacts_migrated += 1

                                

                except Exception as e:

                    print(f"Warning: Error migrating contacts for vendor {new_vendor_id}: {str(e)}")

            

            # Migrate documents if they exist

            documents_migrated = 0

            if temp_vendor.documents:

                try:

                    documents_data = temp_vendor.documents if isinstance(temp_vendor.documents, list) else []

                    

                    for document in documents_data:

                        if document and isinstance(document, dict):

                            document_data = {

                                'vendor_id': new_vendor_id,

                                'document_type': document.get('document_type', 'OTHER'),

                                'document_name': document.get('document_name', ''),

                                'file_name': document.get('file_name', ''),

                                'file_path': document.get('file_path', ''),

                                'file_size': document.get('file_size', 0),

                                'mime_type': document.get('mime_type', ''),

                                'document_category': document.get('document_category', ''),

                                'expiry_date': document.get('expiry_date'),

                                'version_number': document.get('version_number', '1.0'),

                                'status': 'APPROVED',  # Set to APPROVED since this is after final approval

                                'uploaded_by': user_id,

                                'approved_by': user_id,

                                'upload_date': timezone.now(),

                                'approval_date': timezone.now(),

                                'created_at': timezone.now()

                            }

                            

                            # Insert document

                            with connections['default'].cursor() as cursor:

                                doc_columns = list(document_data.keys())

                                doc_placeholders = ['%s'] * len(doc_columns)

                                doc_values = list(document_data.values())

                                

                                doc_insert_query = f"""

                                    INSERT INTO vendor_documents ({', '.join(doc_columns)})

                                    VALUES ({', '.join(doc_placeholders)})

                                """

                                

                                cursor.execute(doc_insert_query, doc_values)

                                documents_migrated += 1

                                

                except Exception as e:

                    print(f"Warning: Error migrating documents for vendor {new_vendor_id}: {str(e)}")

            

            # Update temp vendor status to indicate migration

            temp_vendor.status = 'MIGRATED'

            temp_vendor.save()

            

            return {

                'success': True,

                'vendor_id': new_vendor_id,

                'vendor_code': vendor_data['vendor_code'],

                'company_name': vendor_data['company_name'],

                'contacts_migrated': contacts_migrated,

                'documents_migrated': documents_migrated,

                'message': f'Successfully migrated vendor {vendor_data["company_name"]} with {contacts_migrated} contacts and {documents_migrated} documents'

            }

            

    except TempVendor.DoesNotExist:

        return {

            'success': False,

            'error': f'Temp vendor with ID {temp_vendor_id} not found'

        }

    except Exception as e:

        print(f"Error migrating vendor {temp_vendor_id}: {str(e)}")

        return {

            'success': False,

            'error': f'Failed to migrate vendor: {str(e)}'

        }





def standardize_response_data(response_data, stage_status, decision='', comments='', rejection_reason=''):

    """

    Standardize response_data structure for approval stages to ensure consistent format

    regardless of approval status (APPROVED/REJECTED)

    """

    if not response_data:

        response_data = {}

    

    # If response_data is a string, parse it

    if isinstance(response_data, str):

        try:

            response_data = json.loads(response_data)

        except:

            response_data = {}

    

    # Create standardized structure - preserve existing data and only fill in missing fields

    standardized_data = {

        'comments': response_data.get('comments', comments),

        'decision': response_data.get('decision', decision or stage_status),

        'is_draft': response_data.get('is_draft', False),

        'total_score': response_data.get('total_score', 0),

        'draft_saved_at': response_data.get('draft_saved_at', ''),

        'draft_saved_by': response_data.get('draft_saved_by', ''),

        'reviewer_scores': response_data.get('reviewer_scores', {}),

        'scores_saved_at': response_data.get('scores_saved_at', ''),

        'scores_saved_by': response_data.get('scores_saved_by', ''),

        'rejection_reason': response_data.get('rejection_reason', rejection_reason)

    }

    

    # Debug logging to track data preservation

    if response_data.get('reviewer_scores'):

        print(f"Debug - Preserving reviewer_scores in standardization: {len(response_data['reviewer_scores'])} scores")

        standardized_data['reviewer_scores'] = response_data['reviewer_scores']

    

    if response_data.get('total_score'):

        print(f"Debug - Preserving total_score in standardization: {response_data['total_score']}")

        standardized_data['total_score'] = response_data['total_score']

    

    return standardized_data





def create_approval_version(approval_id, version_type, version_label, json_payload, changes_summary, 

                          created_by, created_by_name, created_by_role, change_reason='', db_connection='tprm'):

    """Helper function to create a new version with proper version numbering
    
    Args:
        db_connection: Database connection to use ('tprm' or 'default'). Defaults to 'tprm'.
    """

    try:
        # Use tprm database connection by default, fallback to default if tprm doesn't exist
        try:
            if db_connection not in connections.databases:
                print(f"Warning: '{db_connection}' database connection not found, falling back to 'default'")
                db_connection = 'default'
        except Exception as db_check_error:
            print(f"Warning: Error checking database connections: {db_check_error}, using 'default'")
            db_connection = 'default'

        with connections[db_connection].cursor() as cursor:

            # Get the maximum version number to ensure proper incrementation

            cursor.execute("""

                SELECT MAX(version_number)

                FROM approval_request_versions 

                WHERE approval_id = %s

            """, [approval_id])

            

            max_version_row = cursor.fetchone()

            

            if max_version_row and max_version_row[0] is not None:

                next_version_number = max_version_row[0] + 1

                

                # Get the current version's ID for parent linkage

                cursor.execute("""

                    SELECT version_id 

                    FROM approval_request_versions 

                    WHERE approval_id = %s AND is_current = 1

                    LIMIT 1

                """, [approval_id])

                

                current_version_row = cursor.fetchone()

                parent_version_id = current_version_row[0] if current_version_row else None

                

                # Mark all previous versions as not current

                cursor.execute("""

                    UPDATE approval_request_versions 

                    SET is_current = 0 

                    WHERE approval_id = %s

                """, [approval_id])

            else:

                # First version

                next_version_number = 1

                parent_version_id = None

            

            # Generate unique version_id

            version_id = str(uuid.uuid4()).replace('-', '').upper()[:16]

            

            # Create new version

            cursor.execute("""

                INSERT INTO approval_request_versions 

                (version_id, approval_id, version_number, version_label, json_payload, 

                 changes_summary, created_by, created_by_name, created_by_role, 

                 version_type, parent_version_id, is_current, is_approved, change_reason, created_at)

                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

            """, [

                version_id, approval_id, next_version_number, version_label,

                json.dumps(json_payload) if json_payload else None,

                changes_summary, created_by, created_by_name, created_by_role,

                version_type, parent_version_id, True, False, change_reason,

                timezone.now()

            ])

            
            # CRITICAL: Commit the transaction to persist the version changes
            connections[db_connection].commit()
            
            print(f"✓ Version created and committed: {version_id} (v{next_version_number})")
            print(f"  - Approval ID: {approval_id}")
            print(f"  - Version Type: {version_type}")
            print(f"  - Version Label: {version_label}")
            print(f"  - Created By: {created_by_name} ({created_by_role})")
            print(f"  - Parent Version: {parent_version_id}")
            
            # Verify the insertion
            cursor.execute("""
                SELECT version_id, version_number, version_label, created_by_name, is_current
                FROM approval_request_versions 
                WHERE approval_id = %s 
                ORDER BY version_number DESC
            """, [approval_id])
            
            all_versions = cursor.fetchall()
            print(f"  - Total versions for approval {approval_id}: {len(all_versions)}")
            for v in all_versions:
                print(f"    * v{v[1]}: {v[2]} by {v[3]} (current: {v[4]})")
            

            return version_id

            

    except Exception as e:

        print(f"Error creating version: {str(e)}")

        return None





def check_sequential_approval_ready(approval_id, stage_order):

    """Check if the current stage can be processed based on sequential approval logic"""

    try:
        # Use tprm database connection for vendor approval queries
        db_connection = 'tprm'
        if 'tprm' not in connections.databases:
            db_connection = 'default'

        with connections[db_connection].cursor() as cursor:

            # Get workflow type

            cursor.execute("""

                SELECT aw.workflow_type 

                FROM approval_requests ar 

                JOIN approval_workflows aw ON ar.workflow_id = aw.workflow_id 

                WHERE ar.approval_id = %s

            """, [approval_id])

            

            workflow_row = cursor.fetchone()

            if not workflow_row:

                return True  # Default to allowing processing

            

            workflow_type = workflow_row[0]

            

            # For multi-level workflows, allow processing without sequential restriction

            if workflow_type == 'MULTI_LEVEL':

                return True  # No sequential restriction for multi-level workflows

            

            # For other workflow types, maintain existing logic if needed

            return True  # Allow processing for all workflow types

            

    except Exception as e:

        print(f"Error checking sequential approval: {str(e)}")

        return False





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_my_approvals(request):

    """Return approvals assigned to a given user, grouped by stage_type.
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation

    Query params:

    - user_id: int (required)

    - include_status: comma-separated statuses to include for stages (default PENDING,IN_PROGRESS)

    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        user_id = request.query_params.get('user_id')

        if not user_id or not str(user_id).isdigit():

            return Response({

                'error': 'user_id query parameter is required and must be numeric'

            }, status=status.HTTP_400_BAD_REQUEST)



        include_status_param = request.query_params.get('include_status')

        include_statuses = None

        if include_status_param and include_status_param.strip().upper() != 'ALL':

            include_statuses = [s.strip().upper() for s in include_status_param.split(',') if s.strip()]

        # Use tprm database connection for vendor approval queries
        import logging
        from django.db import connections as db_connections
        logger = logging.getLogger(__name__)
        
        # Use tprm connection if available, otherwise fall back to default
        if 'tprm' in db_connections.databases:
            db_connection = db_connections['tprm']
            db_name = db_connection.settings_dict.get('NAME', 'tprm_integration')
            logger.info(f"[My Approvals] Using tprm database connection: {db_name} for user_id: {user_id}")
        else:
            db_connection = db_connections['default']
            db_name = db_connection.settings_dict.get('NAME', '')
            logger.warning(f"[My Approvals] tprm connection not found, using default: {db_name}")

        # Initialize rows variable before try block
        rows = []
        
        try:
            with db_connection.cursor() as cursor:

                if include_statuses:

                    cursor.execute(

                        """

                        SELECT 

                            ar.approval_id,

                            ar.workflow_id,

                            ar.request_title,

                            ar.request_description,

                            ar.requester_id,

                            ar.requester_department,

                            ar.priority,

                            ar.overall_status,

                            ar.submission_date,

                            ar.created_at,

                            ar.updated_at,

                            ast.stage_id,

                            ast.stage_order,

                            ast.stage_name,

                            ast.stage_type,

                            ast.stage_status,

                            ast.deadline_date

                        FROM approval_stages ast

                        JOIN approval_requests ar ON ar.approval_id = ast.approval_id
                        
                        JOIN approval_workflows aw ON ar.workflow_id = aw.workflow_id
                        
                        LEFT JOIN temp_vendor tv ON JSON_EXTRACT(ar.request_data, '$.vendor_id') = tv.id

                        WHERE ast.assigned_user_id = %s

                          AND UPPER(ast.stage_status) IN ({statuses})

                          AND aw.business_object_type = 'Vendor'
                          
                          AND (tv.TenantId = %s OR tv.TenantId IS NULL)

                        ORDER BY ast.stage_type, ast.stage_order, ar.created_at DESC

                        """.format(statuses=','.join(['%s'] * len(include_statuses))),

                        [int(user_id), *include_statuses, tenant_id]

                    )

                else:

                    cursor.execute(

                        """

                        SELECT 

                            ar.approval_id,

                            ar.workflow_id,

                            ar.request_title,

                            ar.request_description,

                            ar.requester_id,

                            ar.requester_department,

                            ar.priority,

                            ar.overall_status,

                            ar.submission_date,

                            ar.created_at,

                            ar.updated_at,

                            ast.stage_id,

                            ast.stage_order,

                            ast.stage_name,

                            ast.stage_type,

                            ast.stage_status,

                            ast.deadline_date

                        FROM approval_stages ast

                        JOIN approval_requests ar ON ar.approval_id = ast.approval_id

                        JOIN approval_workflows aw ON ar.workflow_id = aw.workflow_id
                        
                        LEFT JOIN temp_vendor tv ON JSON_EXTRACT(ar.request_data, '$.vendor_id') = tv.id

                        WHERE ast.assigned_user_id = %s

                        AND aw.business_object_type = 'Vendor'
                        
                        AND (tv.TenantId = %s OR tv.TenantId IS NULL)

                        ORDER BY ast.stage_type, ast.stage_order, ar.created_at DESC

                        """,

                        [int(user_id), tenant_id]

                    )



                columns = [col[0] for col in cursor.description]

                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        except Exception as db_error:
            error_msg = str(db_error)
            logger.error(f"[My Approvals] Database error: {error_msg}")
            
            # Check if it's a table not found error for temp_vendor
            if "temp_vendor" in error_msg.lower() and ("doesn't exist" in error_msg.lower() or "does not exist" in error_msg.lower()):
                logger.error(f"[My Approvals] ERROR: temp_vendor table not found in database '{db_name}'. "
                           f"Expected database: 'tprm_integration'. "
                           f"Please ensure the DATABASES['default']['NAME'] is set to 'tprm_integration'.")
                return Response({
                    'error': f'temp_vendor table not found in database. Expected database: tprm_integration, but using: {db_name}',
                    'message': 'Database configuration error. Please check that DB_NAME environment variable is set to tprm_integration.',
                    'database_used': db_name,
                    'database_expected': 'tprm_integration'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Re-raise other database errors
            raise

        parallel = []

        sequential = []

        for row in rows:

            item = {

                'approval_id': row['approval_id'],

                'workflow_id': row['workflow_id'],

                'request_title': row['request_title'],

                'request_description': row['request_description'],

                'priority': row['priority'],

                'overall_status': row['overall_status'],

                'submission_date': row['submission_date'],

                'stage': {

                    'stage_id': row['stage_id'],

                    'stage_order': row['stage_order'],

                    'stage_name': row['stage_name'],

                    'stage_type': row['stage_type'],

                    'stage_status': row['stage_status'],

                    'deadline_date': row['deadline_date'],

                }

            }

            if str(row['stage_type']).upper() == 'PARALLEL':

                parallel.append(item)

            else:

                sequential.append(item)



        return Response({

            'parallel': parallel,

            'sequential': sequential,

            'count': {

                'parallel': len(parallel),

                'sequential': len(sequential)

            }

        }, status=status.HTTP_200_OK)



    except Exception as e:

        print(f"Error fetching my approvals: {str(e)}")

        return Response({

            'error': 'Failed to fetch approvals for user',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_stage_reviewers(request):

    """Return distinct reviewers present in approval_stages for dropdowns.
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation

    Returns id (assigned_user_id) and name (assigned_user_name). Filters out NULL/empty.

    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        # Use tprm database connection where temp_vendor table exists
        db_connection = 'tprm'
        try:
            if 'tprm' not in connections.databases:
                db_connection = 'default'
        except Exception as db_check_error:
            print(f"Warning: Error checking database connections: {db_check_error}, using 'tprm' connection")

        with connections[db_connection].cursor() as cursor:

            cursor.execute(

                """

                SELECT DISTINCT s.assigned_user_id AS id, s.assigned_user_name AS name

                FROM approval_stages s

                JOIN approval_requests a ON s.approval_id = a.approval_id

                JOIN approval_workflows w ON a.workflow_id = w.workflow_id
                
                LEFT JOIN temp_vendor tv ON JSON_EXTRACT(a.request_data, '$.vendor_id') = tv.id

                WHERE s.assigned_user_id IS NOT NULL

                  AND CAST(s.assigned_user_id AS CHAR) <> ''

                  AND w.business_object_type = 'Vendor'
                  
                  AND (tv.TenantId = %s OR tv.TenantId IS NULL)

                ORDER BY name

                """,
                
                [tenant_id]

            )

            reviewers = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]



        return Response(reviewers, status=status.HTTP_200_OK)

    except Exception as e:

        print(f"Error fetching stage reviewers: {str(e)}")

        return Response({

            'error': 'Failed to fetch stage reviewers',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_user_assigned_stages(request, user_id):

    """Return all stages assigned to the given user with request/workflow info.
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        # Use tprm database connection for vendor approval queries
        import logging
        from django.db import connections as db_connections
        logger = logging.getLogger(__name__)
        
        # Use tprm connection if available, otherwise fall back to default
        if 'tprm' in db_connections.databases:
            db_connection = db_connections['tprm']
            db_name = db_connection.settings_dict.get('NAME', 'tprm_integration')
            logger.info(f"[Assigned Stages] Using tprm database connection: {db_name} for user_id: {user_id}")
        else:
            db_connection = db_connections['default']
            db_name = db_connection.settings_dict.get('NAME', '')
            logger.warning(f"[Assigned Stages] tprm connection not found, using default: {db_name}")

        # Initialize stages list
        stages = []
        
        try:
            with db_connection.cursor() as cursor:

                cursor.execute(

                    """

                    SELECT 

                        s.stage_id, s.approval_id, s.stage_order, s.stage_name, s.stage_description,

                        s.assigned_user_id, s.assigned_user_name, s.assigned_user_role, s.department,

                        s.stage_type, s.stage_status, s.deadline_date, s.extended_deadline,

                        s.started_at, s.completed_at, s.response_data, s.rejection_reason,

                        s.escalation_level, s.is_mandatory, s.created_at, s.updated_at,

                        a.request_title, a.request_description, a.requester_id, a.requester_department,

                        a.priority, a.request_data, a.overall_status, a.submission_date,

                        a.created_at AS request_created_at, a.updated_at AS request_updated_at,

                        w.workflow_type

                    FROM approval_stages s

                    JOIN approval_requests a ON s.approval_id = a.approval_id

                    JOIN approval_workflows w ON a.workflow_id = w.workflow_id
                    
                    -- Ensure temp_vendor is read from the current database (should be tprm_integration after connection switch)
                    LEFT JOIN temp_vendor tv ON JSON_EXTRACT(a.request_data, '$.vendor_id') = tv.id

                    WHERE s.assigned_user_id = %s

                    AND w.business_object_type = 'Vendor'
                    
                    AND (tv.TenantId = %s OR tv.TenantId IS NULL)

                    ORDER BY s.created_at DESC

                    """,

                    [user_id, tenant_id]

                )

                columns = [col[0] for col in cursor.description]

                for row in cursor.fetchall():

                    item = dict(zip(columns, row))

                    # Parse JSON fields if strings

                    for json_key in ('response_data', 'request_data'):

                        if item.get(json_key) and isinstance(item.get(json_key), str):

                            try:

                                item[json_key] = json.loads(item[json_key])

                            except Exception:

                                pass

                    stages.append(item)

        except Exception as db_error:
            error_msg = str(db_error)
            logger.error(f"[Assigned Stages] Database error: {error_msg}")
            
            # Check if it's a table not found error for temp_vendor
            if "temp_vendor" in error_msg.lower() and ("doesn't exist" in error_msg.lower() or "does not exist" in error_msg.lower()):
                logger.error(f"[Assigned Stages] ERROR: temp_vendor table not found in database '{db_name}'. "
                           f"Expected database: 'tprm_integration'. "
                           f"Please ensure the DATABASES['default']['NAME'] is set to 'tprm_integration'.")
                return Response({
                    'error': f'temp_vendor table not found in database. Expected database: tprm_integration, but using: {db_name}',
                    'message': 'Database configuration error. Please check that DB_NAME environment variable is set to tprm_integration.',
                    'database_used': db_name,
                    'database_expected': 'tprm_integration'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Re-raise other database errors
            raise

        return Response(stages, status=status.HTTP_200_OK)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching assigned stages: {str(e)}")
        print(f"Error fetching assigned stages: {str(e)}")

        return Response({

            'error': 'Failed to fetch assigned stages',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('approve_reject_vendor')
@require_tenant
@tenant_filter
def post_stage_action(request, stage_id):

    """Approve/Reject/Request Changes for a stage by id.
    MULTI-TENANCY: Ensures stage belongs to tenant's vendor

    Expected payload: { action: APPROVE|REJECT|REQUEST_CHANGES, user_id, user_name, response_data?, rejection_reason?, comments? }

    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        payload = request.data or {}

        action = str(payload.get('action', '')).upper()

        if action not in ('APPROVE', 'REJECT', 'REQUEST_CHANGES'):

            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        # Use tprm database connection for vendor approval queries
        # This ensures data is written to the same database where it's read from
        db_connection = 'tprm'
        try:
            # Check if 'tprm' connection exists
            if 'tprm' not in connections.databases:
                print("Warning: 'tprm' database connection not found, falling back to 'default'")
                db_connection = 'default'
            else:
                print(f"Using 'tprm' database connection for stage action (tprm_integration)")
        except Exception as db_check_error:
            print(f"Warning: Error checking database connections: {db_check_error}, using 'tprm' connection")

        with connections[db_connection].cursor() as cursor:

            # Get current stage + related info + workflow type
            # MULTI-TENANCY: Filter by tenant

            cursor.execute("""

                SELECT as_table.approval_id, as_table.stage_order, as_table.stage_name, as_table.assigned_user_role,

                       aw.workflow_type, ar.request_data

                FROM approval_stages as_table

                JOIN approval_requests ar ON as_table.approval_id = ar.approval_id

                JOIN approval_workflows aw ON ar.workflow_id = aw.workflow_id
                
                LEFT JOIN temp_vendor tv ON JSON_EXTRACT(ar.request_data, '$.vendor_id') = tv.id

                WHERE as_table.stage_id = %s

                AND (tv.TenantId = %s OR tv.TenantId IS NULL)

            """, [stage_id, tenant_id])

            

            row = cursor.fetchone()

            if not row:

                return Response({'error': 'Stage not found'}, status=status.HTTP_404_NOT_FOUND)

            

            approval_id, stage_order, stage_name, user_role, workflow_type, current_request_data = row

            

            # Check sequential approval logic for MULTI_LEVEL workflows

            if workflow_type == 'MULTI_LEVEL' and action in ('APPROVE', 'REJECT'):

                if not check_sequential_approval_ready(approval_id, stage_order):

                    return Response({

                        'error': 'Previous stages must be approved before this stage can be processed'

                    }, status=status.HTTP_400_BAD_REQUEST)



            now_ts = timezone.now()

            user_id = payload.get('user_id', 'unknown')

            user_name = payload.get('user_name', 'Unknown User')



            if action == 'APPROVE':

                # Standardize response data structure

                standardized_response_data = standardize_response_data(

                    response_data=payload.get('response_data', {}),

                    stage_status='APPROVED',

                    decision='APPROVE',

                    comments=payload.get('comments', ''),

                    rejection_reason=''

                )

                

                # Update stage status

                cursor.execute("""

                    UPDATE approval_stages

                    SET stage_status='APPROVED', completed_at=%s, response_data=%s, updated_at=%s

                    WHERE stage_id=%s

                """, [now_ts, json.dumps(standardized_response_data), now_ts, stage_id])



                # For MULTI_LEVEL workflows, check if this completes the workflow

                if workflow_type == 'MULTI_LEVEL':

                    # Check if this is the last stage

                    cursor.execute("""

                        SELECT COUNT(*) FROM approval_stages 

                        WHERE approval_id = %s AND stage_order > %s

                    """, [approval_id, stage_order])

                    

                    remaining_stages = cursor.fetchone()[0]

                    

                    if remaining_stages == 0:

                        # This is the last stage - mark workflow as APPROVED

                        cursor.execute("""

                            UPDATE approval_requests 

                            SET overall_status='APPROVED', completion_date=%s, updated_at=%s 

                            WHERE approval_id=%s

                        """, [now_ts, now_ts, approval_id])



                        # Check if this is a final vendor approval and trigger migration

                        if current_request_data:

                            try:

                                request_data_obj = json.loads(current_request_data) if isinstance(current_request_data, str) else current_request_data

                                rd = request_data_obj.get('request_data', {})

                                approval_type = rd.get('approval_type', '').lower().replace(' ', '_')

                                vendor_id = rd.get('vendor_id')



                                print(f"Debug - Final approval check: type={approval_type}, vendor_id={vendor_id}")



                                if approval_type == 'final_vendor_approval' and vendor_id:

                                    print(f"Starting vendor migration for final vendor approval: {approval_id}, vendor_id: {vendor_id}")

                                    migration_result = migrate_vendor_from_temp_to_main(vendor_id, user_id)

                                    print(f"Migration result: {migration_result}")

                            except Exception as e:

                                print(f"Error during vendor migration check: {str(e)}")

                        

                        # Update vendor lifecycle stage on approval completion
                        try:
                            # Parse request data to get vendor ID if available
                            if current_request_data:
                                request_data_obj = json.loads(current_request_data) if isinstance(current_request_data, str) else current_request_data
                                vendor_id = request_data_obj.get('vendor_id') or request_data_obj.get('request_data', {}).get('vendor_id')
                                
                                # Try to extract vendor_id from questionnaire_assignment_id if needed
                                if not vendor_id:
                                    rd = request_data_obj.get('request_data', request_data_obj)
                                    approval_type_check = rd.get('approval_type', '').lower().replace(' ', '_')
                                    
                                    if approval_type_check in ('questionnaire_approval', 'response_approval'):
                                        questionnaire_assignment_id = rd.get('questionnaire_assignment_id')
                                        if questionnaire_assignment_id:
                                            try:
                                                from tprm_backend.apps.vendor_questionnaire.models import QuestionnaireAssignments
                                                assignment = QuestionnaireAssignments.objects.get(assignment_id=questionnaire_assignment_id)
                                                if assignment.temp_vendor:
                                                    vendor_id = assignment.temp_vendor.id
                                                    print(f"Debug - Extracted vendor_id {vendor_id} from questionnaire_assignment_id {questionnaire_assignment_id} (multi-level)")
                                            except Exception as e:
                                                print(f"ERROR - Failed to extract vendor_id from assignment: {str(e)}")
                                
                                if vendor_id:
                                    # Determine the lifecycle transition based on approval type
                                    rd = request_data_obj.get('request_data', request_data_obj)
                                    approval_type = rd.get('approval_type', '').lower().replace(' ', '_')
                                    
                                    print(f"Debug - Multi-level approval completed for vendor {vendor_id}, type: {approval_type}")
                                    
                                    if approval_type == 'questionnaire_approval':
                                        # End Questionnaire Approval and start Questionnaire Response
                                        print(f"Initiating Questionnaire Approval completion for vendor {vendor_id} (multi-level workflow)")
                                        try:
                                            from tprm_backend.apps.vendor_core.models import LifecycleTracker, TempVendor
                                            from tprm_backend.apps.vendor_core.views import get_lifecycle_stage_id_by_code
                                            
                                            current_time = timezone.now()
                                            ques_approval_stage_id = get_lifecycle_stage_id_by_code('QUES_APP')
                                            ques_response_stage_id = get_lifecycle_stage_id_by_code('QUES_RES')
                                            
                                            if ques_approval_stage_id and ques_response_stage_id:
                                                # End Questionnaire Approval stage
                                                approval_entry = LifecycleTracker.objects.filter(
                                                    vendor_id=vendor_id,
                                                    lifecycle_stage=ques_approval_stage_id,
                                                    ended_at__isnull=True
                                                ).first()
                                                
                                                if approval_entry:
                                                    approval_entry.ended_at = current_time
                                                    approval_entry.save()
                                                    print(f"✓ Ended Questionnaire Approval stage for vendor {vendor_id}")
                                                
                                                # Start Questionnaire Response stage
                                                LifecycleTracker.objects.create(
                                                    vendor_id=vendor_id,
                                                    lifecycle_stage=ques_response_stage_id,
                                                    started_at=current_time
                                                )
                                                
                                                # Update temp vendor
                                                temp_vendor = TempVendor.objects.get(id=vendor_id)
                                                temp_vendor.lifecycle_stage = ques_response_stage_id
                                                temp_vendor.save()
                                                
                                                print(f"✓ Started Questionnaire Response stage for vendor {vendor_id}")
                                        except Exception as e:
                                            print(f"ERROR - Failed to update lifecycle from QUES_APP to QUES_RES: {str(e)}")
                                    elif approval_type == 'response_approval':
                                        # End Response Approval and start Vendor Approval
                                        print(f"Initiating Response Approval completion for vendor {vendor_id} (multi-level workflow)")
                                        _end_response_approval_start_vendor_approval(vendor_id)
                                        print(f"✓ Response Approval lifecycle stage completed for vendor {vendor_id}")
                                    elif approval_type in ('vendor_approval', 'final_vendor_approval'):
                                        # End Vendor Approval stage (final completion)
                                        print(f"Initiating Vendor Approval completion for vendor {vendor_id} (multi-level workflow)")
                                        _end_vendor_approval_stage(vendor_id)
                                        print(f"✓ Vendor Approval lifecycle stage completed for vendor {vendor_id}")
                                    else:
                                        print(f"Unknown approval type: {approval_type} for vendor {vendor_id}")
                                else:
                                    print(f"WARNING - Could not extract vendor_id for lifecycle tracking in multi-level workflow")
                        except Exception as e:
                            # Don't fail the approval process if lifecycle stage update fails
                            print(f"ERROR - Failed to update vendor lifecycle stage on approval completion: {str(e)}")
                            import traceback
                            traceback.print_exc()

                        

                        # Create final version

                        create_approval_version(

                            approval_id=approval_id,

                            version_type='FINAL',

                            version_label=f'Workflow Completed - All Stages Approved',

                            json_payload=current_request_data,

                            changes_summary='Final approval - workflow completed successfully',

                            created_by=user_id,

                            created_by_name=user_name,

                            created_by_role=user_role,

                            change_reason='Workflow completion'

                        )

                    else:

                        # Create version record for intermediate stage approval

                        create_approval_version(

                            approval_id=approval_id,

                            version_type='REVISION',

                            version_label=f'Stage {stage_order}: {stage_name} - Approved',

                            json_payload=current_request_data,

                            changes_summary=f'Stage {stage_order} ({stage_name}) approved by {user_name} ({user_role}). Comments: {payload.get("comments", "None")}',

                            created_by=user_id,

                            created_by_name=user_name,

                            created_by_role=user_role,

                            change_reason=f'Stage {stage_order} approval'

                        )

                        

                        # Activate next stage

                        cursor.execute("""

                            UPDATE approval_stages 

                            SET stage_status='IN_PROGRESS', started_at=%s, updated_at=%s

                            WHERE approval_id = %s AND stage_order = %s

                        """, [now_ts, now_ts, approval_id, stage_order + 1])



            elif action == 'REJECT':

                # Standardize response data structure

                standardized_response_data = standardize_response_data(

                    response_data=payload.get('response_data', {}),

                    stage_status='REJECTED',

                    decision='REJECT',

                    comments=payload.get('comments', ''),

                    rejection_reason=payload.get('rejection_reason', '')

                )

                

                # Update stage status

                cursor.execute("""

                    UPDATE approval_stages

                    SET stage_status='REJECTED', completed_at=%s, rejection_reason=%s, response_data=%s, updated_at=%s

                    WHERE stage_id=%s

                """, [now_ts, payload.get('rejection_reason', ''), json.dumps(standardized_response_data), now_ts, stage_id])



                # For multi-level: set overall request to PENDING (awaiting admin decision)

                if workflow_type == 'MULTI_LEVEL':

                    cursor.execute("""

                        UPDATE approval_requests 

                        SET overall_status='PENDING', updated_at=%s 

                        WHERE approval_id=%s

                    """, [now_ts, approval_id])

                    

                    # Create version record for rejection

                    create_approval_version(

                        approval_id=approval_id,

                        version_type='REVISION',

                        version_label=f'Stage {stage_name} Rejected',

                        json_payload=current_request_data,

                        changes_summary=f'Stage {stage_name} rejected: {payload.get("rejection_reason", "")}',

                        created_by=user_id,

                        created_by_name=user_name,

                        created_by_role=user_role,

                        change_reason=payload.get("rejection_reason", "")

                    )



            elif action == 'REQUEST_CHANGES':

                # Get current request data for version creation

                revised_data = payload.get('response_data', {})

                

                # Standardize response data structure

                standardized_response_data = standardize_response_data(

                    response_data=revised_data,

                    stage_status='PENDING',

                    decision='REQUEST_CHANGES',

                    comments=payload.get('comments', ''),

                    rejection_reason=''

                )

                

                # Update stage status to pending for revision

                cursor.execute("""

                    UPDATE approval_stages

                    SET stage_status='PENDING', completed_at=NULL, response_data=%s, updated_at=%s

                    WHERE stage_id=%s

                """, [json.dumps(standardized_response_data), now_ts, stage_id])



                # For MULTI_LEVEL workflows, implement version control

                if workflow_type == 'MULTI_LEVEL':

                    # Create version record for changes

                    create_approval_version(

                        approval_id=approval_id,

                        version_type='REVISION',

                        version_label=f'Stage {stage_name} - Changes Requested',

                        json_payload=revised_data,

                        changes_summary=payload.get('comments', 'Changes requested'),

                        created_by=user_id,

                        created_by_name=user_name,

                        created_by_role=user_role,

                        change_reason=payload.get('comments', 'Changes requested')

                    )

                    

                    # Reset stages from current stage onwards

                    cursor.execute("""

                        UPDATE approval_stages 

                        SET stage_status='PENDING', completed_at=NULL, response_data=NULL, 

                            rejection_reason=NULL, started_at=NULL

                        WHERE approval_id = %s AND stage_order >= %s

                    """, [approval_id, stage_order])

                    

                    # Set current stage to IN_PROGRESS for revision

                    cursor.execute("""

                        UPDATE approval_stages 

                        SET stage_status='IN_PROGRESS', started_at=%s

                        WHERE stage_id = %s

                    """, [now_ts, stage_id])

                    

                    # Update overall request status

                    cursor.execute("""

                        UPDATE approval_requests 

                        SET overall_status='IN_PROGRESS', updated_at=%s 

                        WHERE approval_id=%s

                    """, [now_ts, approval_id])

        # Commit using the same connection that was used for the cursor
        connections[db_connection].commit()

        return Response({'message': 'Action processed successfully'}, status=status.HTTP_200_OK)

    except Exception as e:

        print(f"Error processing stage action: {str(e)}")

        return Response({

            'error': 'Failed to process stage action',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_questionnaire_questions(request, questionnaire_id: int):

    """Return questions for a given questionnaire_id from questionnaire_questions table.
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation (if tenant_id is available)

    Response is ordered by display_order.

    """

    try:
        # Try to get tenant_id, but don't fail if it's not available
        tenant_id = None
        try:
            tenant_id = get_tenant_id_from_request(request)
        except Exception as tenant_error:
            print(f"Warning: Could not get tenant_id: {str(tenant_error)}")
            tenant_id = None

        # Use tprm database connection for vendor approval queries
        import logging
        from django.db import connections as db_connections
        logger = logging.getLogger(__name__)
        
        # Use tprm connection if available, otherwise fall back to default
        if 'tprm' in db_connections.databases:
            db_connection = db_connections['tprm']
            db_name = db_connection.settings_dict.get('NAME', 'tprm_integration')
            logger.info(f"[Get Questionnaire Questions] Using tprm database connection: {db_name} for questionnaire_id: {questionnaire_id}")
        else:
            db_connection = db_connections['default']
            db_name = db_connection.settings_dict.get('NAME', '')
            logger.warning(f"[Get Questionnaire Questions] tprm connection not found, using default: {db_name}")

        # Use raw SQL query with proper tenant filtering and error handling
        questions = []
        
        try:
            with db_connection.cursor() as cursor:
                # Build query - try with tenant filter if tenant_id is available
                if tenant_id:
                    # Try with tenant filter first
                    try:
                        cursor.execute(
                            """
                            SELECT 
                                question_id, questionnaire_id, question_text, question_type,
                                question_category, is_required, display_order, scoring_weight,
                                options, conditional_logic, help_text
                            FROM questionnaire_questions
                            WHERE questionnaire_id = %s AND (TenantId = %s OR TenantId IS NULL)
                            ORDER BY display_order ASC, question_id ASC
                            """,
                            [questionnaire_id, tenant_id]
                        )
                    except Exception as tenant_error:
                        # If tenant filter fails (e.g., column doesn't exist), try without tenant filter
                        print(f"Warning: Tenant filter query failed: {str(tenant_error)}, trying without tenant filter")
                        cursor.execute(
                            """
                            SELECT 
                                question_id, questionnaire_id, question_text, question_type,
                                question_category, is_required, display_order, scoring_weight,
                                options, conditional_logic, help_text
                            FROM questionnaire_questions
                            WHERE questionnaire_id = %s
                            ORDER BY display_order ASC, question_id ASC
                            """,
                            [questionnaire_id]
                        )
                else:
                    # No tenant_id, just query by questionnaire_id
                    cursor.execute(
                        """
                        SELECT 
                            question_id, questionnaire_id, question_text, question_type,
                            question_category, is_required, display_order, scoring_weight,
                            options, conditional_logic, help_text
                        FROM questionnaire_questions
                        WHERE questionnaire_id = %s
                        ORDER BY display_order ASC, question_id ASC
                        """,
                        [questionnaire_id]
                    )

                columns = [col[0] for col in cursor.description]
                
                for row in cursor.fetchall():
                    q = dict(zip(columns, row))

                    # Parse JSON fields if present and are strings
                    for k in ('options', 'conditional_logic'):
                        if q.get(k) and isinstance(q.get(k), str):
                            try:
                                q[k] = json.loads(q[k])
                            except Exception:
                                pass

                    # Convert Decimal to float for JSON serialization
                    if 'scoring_weight' in q and q['scoring_weight'] is not None:
                        try:
                            q['scoring_weight'] = float(q['scoring_weight'])
                        except (ValueError, TypeError):
                            q['scoring_weight'] = 1.0

                    questions.append(q)

            if not questions:
                print(f"Warning: No questions found for questionnaire_id={questionnaire_id}, tenant_id={tenant_id}")
                return Response({
                    'error': 'No questions found for this questionnaire',
                    'questionnaire_id': questionnaire_id
                }, status=status.HTTP_404_NOT_FOUND)

            return Response(questions, status=status.HTTP_200_OK)
            
        except Exception as query_error:
            print(f"Error executing SQL query: {str(query_error)}")
            import traceback
            print(traceback.format_exc())
            raise query_error

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error fetching questionnaire questions: {str(e)}")
        print(f"Traceback: {error_trace}")
        
        return Response({
            'error': 'Failed to fetch questionnaire questions',
            'details': str(e),
            'questionnaire_id': questionnaire_id,
            'tenant_id': tenant_id if 'tenant_id' in locals() else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_approvals_by_requester(request):

    """Return all approval requests created by a requester.
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation

    Query params:

    - requester_id: int (required)

    - stage_type: All|Parallel|Sequential (optional, defaults to All)



    Uses approval_requests joined with approval_workflows to determine flow type

    (MULTI_PERSON -> Parallel, MULTI_LEVEL -> Sequential) and counts stages.

    """

    try:
        # Use tprm database connection for vendor approval queries
        import logging
        from django.db import connections as db_connections
        logger = logging.getLogger(__name__)
        
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        requester_id = request.query_params.get('requester_id')

        if requester_id is None or str(requester_id).strip() == '':

            return Response({'error': 'requester_id query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Convert requester_id to integer for proper comparison
        try:
            requester_id_int = int(requester_id)
            logger.info(f"[Get Approvals By Requester] Processing request for requester_id: {requester_id_int} (original: {requester_id})")
        except (ValueError, TypeError):
            logger.error(f"[Get Approvals By Requester] Invalid requester_id: {requester_id}")
            return Response({'error': 'requester_id must be a valid integer'}, status=status.HTTP_400_BAD_REQUEST)

        stage_type = str(request.query_params.get('stage_type', 'ALL')).upper()

        flow_filter = None

        if stage_type == 'PARALLEL':

            flow_filter = 'MULTI_PERSON'

        elif stage_type == 'SEQUENTIAL':

            flow_filter = 'MULTI_LEVEL'
        
        # Use tprm connection if available, otherwise fall back to default
        if 'tprm' in db_connections.databases:
            db_connection = db_connections['tprm']
            db_name = db_connection.settings_dict.get('NAME', 'tprm_integration')
            logger.info(f"[Get Approvals By Requester] Using tprm database connection: {db_name} for requester_id: {requester_id}")
        else:
            db_connection = db_connections['default']
            db_name = db_connection.settings_dict.get('NAME', '')
            logger.warning(f"[Get Approvals By Requester] tprm connection not found, using default: {db_name}")
        
        with db_connection.cursor() as cursor:
            # Check if TenantId column exists in approval_requests table
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'approval_requests' 
                AND COLUMN_NAME = 'TenantId'
            """)
            has_tenant_id_column = cursor.fetchone()[0] > 0
            logger.info(f"[Get Approvals By Requester] approval_requests.TenantId column exists: {has_tenant_id_column}")
            
            # Build SQL query - prefer filtering by TenantId column if it exists
            if has_tenant_id_column:
                # Check if TenantId also exists in approval_workflows
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'approval_workflows' 
                    AND COLUMN_NAME = 'TenantId'
                """)
                workflow_has_tenant_id = cursor.fetchone()[0] > 0
                logger.info(f"[Get Approvals By Requester] approval_workflows.TenantId column exists: {workflow_has_tenant_id}")
                
                # Filter directly by TenantId - check both approval_requests and approval_workflows
                if workflow_has_tenant_id:
                    # Both tables have TenantId - check either one matches
                    sql = (
                        """
                        SELECT 
                            ar.approval_id,
                            ar.request_title,
                            ar.priority,
                            ar.overall_status,
                            ar.submission_date,
                            ar.created_at,
                            ar.updated_at,
                            w.workflow_type,
                            COUNT(s.stage_id) AS stage_count
                        FROM approval_requests ar
                        JOIN approval_workflows w ON w.workflow_id = ar.workflow_id
                        LEFT JOIN approval_stages s ON s.approval_id = ar.approval_id
                        WHERE ar.requester_id = %s
                        AND w.business_object_type = 'Vendor'
                        AND (ar.TenantId = %s OR w.TenantId = %s OR (ar.TenantId IS NULL AND w.TenantId IS NULL))
                        {flow_clause}
                        GROUP BY 
                            ar.approval_id, ar.request_title, ar.priority, ar.overall_status,
                            ar.submission_date, ar.created_at, ar.updated_at, w.workflow_type
                        ORDER BY ar.created_at DESC
                        """
                    )
                    params = [requester_id_int, tenant_id, tenant_id]
                else:
                    # Only approval_requests has TenantId
                    sql = (
                        """
                        SELECT 
                            ar.approval_id,
                            ar.request_title,
                            ar.priority,
                            ar.overall_status,
                            ar.submission_date,
                            ar.created_at,
                            ar.updated_at,
                            w.workflow_type,
                            COUNT(s.stage_id) AS stage_count
                        FROM approval_requests ar
                        JOIN approval_workflows w ON w.workflow_id = ar.workflow_id
                        LEFT JOIN approval_stages s ON s.approval_id = ar.approval_id
                        WHERE ar.requester_id = %s
                        AND w.business_object_type = 'Vendor'
                        AND (ar.TenantId = %s OR ar.TenantId IS NULL)
                        {flow_clause}
                        GROUP BY 
                            ar.approval_id, ar.request_title, ar.priority, ar.overall_status,
                            ar.submission_date, ar.created_at, ar.updated_at, w.workflow_type
                        ORDER BY ar.created_at DESC
                        """
                    )
                    params = [requester_id_int, tenant_id]
            else:
                # Fallback: Check if temp_vendor table exists for tenant filtering
                cursor.execute("SHOW TABLES LIKE 'temp_vendor'")
                temp_vendor_exists = cursor.fetchone() is not None
                logger.info(f"[Get Approvals By Requester] temp_vendor table exists: {temp_vendor_exists}")
                
                if temp_vendor_exists:
                    # Use temp_vendor for tenant filtering (legacy approach)
                    sql = (
                        """
                        SELECT 
                            ar.approval_id,
                            ar.request_title,
                            ar.priority,
                            ar.overall_status,
                            ar.submission_date,
                            ar.created_at,
                            ar.updated_at,
                            w.workflow_type,
                            COUNT(s.stage_id) AS stage_count
                        FROM approval_requests ar
                        JOIN approval_workflows w ON w.workflow_id = ar.workflow_id
                        LEFT JOIN approval_stages s ON s.approval_id = ar.approval_id
                        LEFT JOIN temp_vendor tv ON JSON_EXTRACT(ar.request_data, '$.vendor_id') = tv.id
                        WHERE ar.requester_id = %s
                        AND w.business_object_type = 'Vendor'
                        AND (tv.TenantId = %s OR tv.TenantId IS NULL OR tv.id IS NULL)
                        {flow_clause}
                        GROUP BY 
                            ar.approval_id, ar.request_title, ar.priority, ar.overall_status,
                            ar.submission_date, ar.created_at, ar.updated_at, w.workflow_type
                        ORDER BY ar.created_at DESC
                        """
                    )
                    params = [requester_id_int, tenant_id]
                else:
                    # No tenant filtering available - return all requests for requester
                    sql = (
                        """
                        SELECT 
                            ar.approval_id,
                            ar.request_title,
                            ar.priority,
                            ar.overall_status,
                            ar.submission_date,
                            ar.created_at,
                            ar.updated_at,
                            w.workflow_type,
                            COUNT(s.stage_id) AS stage_count
                        FROM approval_requests ar
                        JOIN approval_workflows w ON w.workflow_id = ar.workflow_id
                        LEFT JOIN approval_stages s ON s.approval_id = ar.approval_id
                        WHERE ar.requester_id = %s
                        AND w.business_object_type = 'Vendor'
                        {flow_clause}
                        GROUP BY 
                            ar.approval_id, ar.request_title, ar.priority, ar.overall_status,
                            ar.submission_date, ar.created_at, ar.updated_at, w.workflow_type
                        ORDER BY ar.created_at DESC
                        """
                    )
                    params = [requester_id_int]

            flow_clause = ''
            if flow_filter:
                flow_clause = 'AND w.workflow_type = %s'
                params.append(flow_filter)

            logger.info(f"[Get Approvals By Requester] Executing query with params: {params}, flow_filter: {flow_filter}")
            cursor.execute(sql.format(flow_clause=flow_clause), params)
            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            logger.info(f"[Get Approvals By Requester] Found {len(rows)} approval requests for requester_id: {requester_id_int}")



        data = []

        for r in rows:

            flow = 'Parallel' if str(r.get('workflow_type', '')).upper() == 'MULTI_PERSON' else 'Sequential'

            data.append({

                'approval_id': r['approval_id'],

                'request_title': r['request_title'],

                'priority': r['priority'],

                'overall_status': r['overall_status'],

                'submission_date': r['submission_date'],

                'stage_count': r['stage_count'],

                'flow_type': flow

            })



        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        error_msg = str(e)
        logger.error(f"[Get Approvals By Requester] Error: {error_msg}")
        
        # Check if it's a table not found error
        if "temp_vendor" in error_msg.lower() and ("doesn't exist" in error_msg.lower() or "does not exist" in error_msg.lower()):
            logger.warning(f"[Get Approvals By Requester] temp_vendor table not found, but should have been handled. Error: {error_msg}")
            # Return empty result instead of error if temp_vendor doesn't exist
            return Response([], status=status.HTTP_200_OK)
        
        print(f"Error fetching approvals by requester: {error_msg}")
        return Response({
            'error': 'Failed to fetch approvals by requester',
            'details': error_msg
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_current_user(request):
    """Get current authenticated user information from JWT token.
    MULTI-TENANCY: Returns user info with tenant context
    """
    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        # Get user from JWT authentication
        user = request.user
        
        # Return user information
        user_data = {
            'id': user.id if hasattr(user, 'id') else None,
            'username': user.username if hasattr(user, 'username') else '',
            'email': user.email if hasattr(user, 'email') else '',
            'first_name': user.first_name if hasattr(user, 'first_name') else '',
            'last_name': user.last_name if hasattr(user, 'last_name') else '',
            'department': getattr(user, 'department', ''),
            'role': getattr(user, 'role', ''),
        }
        
        return Response(user_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Error fetching current user: {str(e)}")
        return Response({
            'error': 'Failed to fetch user information',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_users(request):

    """Get all users for dropdown selection
    MULTI-TENANCY: Note - Users may be shared across tenants, but filtering is applied where relevant
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        with connections['default'].cursor() as cursor:

            cursor.execute("""

                SELECT UserId, UserName, Email, CreatedAt 

                FROM users 

                ORDER BY UserName

            """)

            columns = [col[0] for col in cursor.description]

            users = [dict(zip(columns, row)) for row in cursor.fetchall()]

            

            # Add mock data for additional fields needed by frontend

            for user in users:

                user['id'] = user['UserId']

                user['first_name'] = user['UserName'].split(' ')[0] if ' ' in user['UserName'] else user['UserName']

                user['last_name'] = user['UserName'].split(' ')[1] if ' ' in user['UserName'] else ''

                user['role'] = 'Manager' if 'admin' in user['UserName'].lower() else 'Employee'

                user['department'] = 'IT' if 'admin' in user['UserName'].lower() else 'Operations'

            

            return Response(users, status=status.HTTP_200_OK)

            

    except Exception as e:

        print(f"Error fetching users: {str(e)}")

        # Return mock data if database fails

        mock_users = [

            {

                'id': 1,

                'UserId': 1,

                'UserName': 'John Admin',

                'Email': 'john.admin@company.com',

                'first_name': 'John',

                'last_name': 'Admin',

                'role': 'Manager',

                'department': 'IT'

            },

            {

                'id': 2,

                'UserId': 2,

                'UserName': 'Jane Manager',

                'Email': 'jane.manager@company.com',

                'first_name': 'Jane',

                'last_name': 'Manager',

                'role': 'Manager',

                'department': 'Operations'

            },

            {

                'id': 3,

                'UserId': 3,

                'UserName': 'Bob Employee',

                'Email': 'bob.employee@company.com',

                'first_name': 'Bob',

                'last_name': 'Employee',

                'role': 'Employee',

                'department': 'Finance'

            }

        ]

        return Response(mock_users, status=status.HTTP_200_OK)





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_request_with_stages(request, approval_id: str):

    """Return a single approval request with its stages, parsed request_data, and questionnaire questions if applicable.
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        # Use tprm database connection for vendor approval queries
        import logging
        from django.db import connections as db_connections
        logger = logging.getLogger(__name__)
        
        # Use tprm connection if available, otherwise fall back to default
        if 'tprm' in db_connections.databases:
            db_connection = db_connections['tprm']
            db_name = db_connection.settings_dict.get('NAME', 'tprm_integration')
            logger.info(f"[Get Request With Stages] Using tprm database connection: {db_name} for approval_id: {approval_id}")
        else:
            db_connection = db_connections['default']
            db_name = db_connection.settings_dict.get('NAME', '')
            logger.warning(f"[Get Request With Stages] tprm connection not found, using default: {db_name}")

        with db_connection.cursor() as cursor:
            # Check if temp_vendor table exists
            cursor.execute("SHOW TABLES LIKE 'temp_vendor'")
            temp_vendor_exists = cursor.fetchone() is not None
            
            # Build SQL query based on whether temp_vendor table exists
            if temp_vendor_exists:
                cursor.execute(
                    """
                    SELECT 
                        a.approval_id, a.workflow_id, a.request_title, a.request_description,
                        a.requester_id, a.requester_department, a.priority, a.request_data,
                        a.overall_status, a.submission_date, a.completion_date, a.created_at,
                        w.workflow_type, w.workflow_name
                    FROM approval_requests a
                    JOIN approval_workflows w ON a.workflow_id = w.workflow_id
                    LEFT JOIN temp_vendor tv ON JSON_EXTRACT(a.request_data, '$.vendor_id') = tv.id
                    WHERE a.approval_id = %s
                    AND w.business_object_type = 'Vendor'
                    AND (tv.TenantId = %s OR tv.TenantId IS NULL)
                    """,
                    [approval_id, tenant_id]
                )
            else:
                # If temp_vendor doesn't exist, query without tenant filtering via temp_vendor
                cursor.execute(
                    """
                    SELECT 
                        a.approval_id, a.workflow_id, a.request_title, a.request_description,
                        a.requester_id, a.requester_department, a.priority, a.request_data,
                        a.overall_status, a.submission_date, a.completion_date, a.created_at,
                        w.workflow_type, w.workflow_name
                    FROM approval_requests a
                    JOIN approval_workflows w ON a.workflow_id = w.workflow_id
                    WHERE a.approval_id = %s
                    AND w.business_object_type = 'Vendor'
                    """,
                    [approval_id]
                )

            row = cursor.fetchone()

            if not row:

                return Response({'error': 'Approval request not found'}, status=status.HTTP_404_NOT_FOUND)



            columns = [col[0] for col in cursor.description]

            req = dict(zip(columns, row))

            

            # Parse request_data JSON

            if req.get('request_data') and isinstance(req.get('request_data'), str):

                try:

                    req['request_data'] = json.loads(req['request_data'])

                except Exception:

                    pass



            # Get stages with detailed information

            cursor.execute(

                """

                SELECT 

                    stage_id, approval_id, stage_order, stage_name, stage_description,

                    assigned_user_id, assigned_user_name, assigned_user_role, department,

                    stage_type, stage_status, deadline_date, extended_deadline,

                    started_at, completed_at, response_data, rejection_reason,

                    escalation_level, is_mandatory, created_at, updated_at

                FROM approval_stages

                WHERE approval_id = %s

                ORDER BY stage_order

                """,

                [approval_id]

            )

            stage_cols = [c[0] for c in cursor.description]

            stages = []

            for s in cursor.fetchall():

                sd = dict(zip(stage_cols, s))

                if sd.get('response_data') and isinstance(sd.get('response_data'), str):

                    try:

                        sd['response_data'] = json.loads(sd['response_data'])

                    except Exception:

                        pass

                stages.append(sd)



            # Check if this is a questionnaire approval and fetch questions

            # request_data can be nested as { request_data: {...} } or flat; handle both

            questionnaire_questions = []

            request_data = req.get('request_data', {})

            rd = request_data.get('request_data', request_data) if isinstance(request_data, dict) else {}

            approval_type = str(rd.get('approval_type', '')).lower().replace(' ', '_')

            questionnaire_id = rd.get('questionnaire_id')

            

            # Support both 'questionnaire approval' (space) and 'questionnaire_approval' (underscore)

            if approval_type == 'questionnaire_approval' and questionnaire_id:

                try:

                    cursor.execute(

                        """

                        SELECT 

                            question_id, questionnaire_id, question_text, question_type,

                            question_category, is_required, display_order, scoring_weight,

                            options, conditional_logic, help_text

                        FROM questionnaire_questions

                        WHERE questionnaire_id = %s

                        ORDER BY display_order ASC

                        """,

                        [questionnaire_id]

                    )

                    q_columns = [col[0] for col in cursor.description]

                    for q_row in cursor.fetchall():

                        q_data = dict(zip(q_columns, q_row))

                        # Parse JSON fields if present and are strings

                        for k in ('options', 'conditional_logic'):

                            if q_data.get(k) and isinstance(q_data.get(k), str):

                                try:

                                    q_data[k] = json.loads(q_data[k])

                                except Exception:

                                    pass

                        questionnaire_questions.append(q_data)

                except Exception as e:

                    print(f"Error fetching questionnaire questions: {str(e)}")



        req['stages'] = stages

        req['questionnaire_questions'] = questionnaire_questions

        req['is_questionnaire_approval'] = approval_type in ('questionnaire approval', 'questionnaire_approval')

        

        return Response(req, status=status.HTTP_200_OK)

    except Exception as e:

        print(f"Error fetching request with stages: {str(e)}")

        return Response({'error': 'Failed to fetch request with stages', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('approve_reject_vendor')
@require_tenant
@tenant_filter
def requester_final_decision(request, approval_id: str):

    """Allow requester to take final decision on MULTI_PERSON workflows.
    MULTI-TENANCY: Ensures approval belongs to tenant's vendor

    Payload: { decision: APPROVE|REJECT, reason?: str, overall_score_override?: object }

    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        data = request.data or {}

        decision = str(data.get('decision', '')).upper()

        reason = data.get('reason', '')

        overall_score_override = data.get('overall_score_override')

        

        # Get user_id from request (needed for tracking)

        user_id = request.user.id if hasattr(request.user, 'id') and request.user.id else 'anonymous'

        

        if decision not in ('APPROVE', 'REJECT'):

            return Response({'error': 'decision must be APPROVE or REJECT'}, status=status.HTTP_400_BAD_REQUEST)



        # Use tprm database connection for vendor approval queries
        # This ensures data is written to the same database where it's read from
        db_connection = 'tprm'
        try:
            # Check if 'tprm' connection exists
            if 'tprm' not in connections.databases:
                print("Warning: 'tprm' database connection not found, falling back to 'default'")
                db_connection = 'default'
            else:
                print(f"Using 'tprm' database connection for requester final decision (tprm_integration)")
        except Exception as db_check_error:
            print(f"Warning: Error checking database connections: {db_check_error}, using 'tprm' connection")

        with connections[db_connection].cursor() as cursor:
            # MULTI-TENANCY: Filter by tenant
            # Try to use TenantId column directly if it exists, otherwise fall back to temp_vendor join
            try:
                cursor.execute("""
                    SELECT ar.workflow_id, ar.overall_status, ar.request_data 
                    FROM approval_requests ar
                    WHERE ar.approval_id=%s
                    AND (ar.TenantId = %s OR ar.TenantId IS NULL)
                """, [approval_id, tenant_id])
            except Exception as e:
                # Fallback to temp_vendor join if TenantId column doesn't exist
                print(f"TenantId column not found, using temp_vendor join: {str(e)}")
                cursor.execute("""
                    SELECT ar.workflow_id, ar.overall_status, ar.request_data 
                    FROM approval_requests ar
                    LEFT JOIN temp_vendor tv ON JSON_EXTRACT(ar.request_data, '$.vendor_id') = tv.id
                    WHERE ar.approval_id=%s
                    AND (tv.TenantId = %s OR tv.TenantId IS NULL OR tv.id IS NULL)
                """, [approval_id, tenant_id])

            r = cursor.fetchone()

            if not r:

                return Response({'error': 'Approval request not found'}, status=status.HTTP_404_NOT_FOUND)

            workflow_id, overall_status, request_data = r



            cursor.execute("SELECT workflow_type FROM approval_workflows WHERE workflow_id=%s", [workflow_id])

            wf = cursor.fetchone()

            if not wf:

                return Response({'error': 'Workflow not found'}, status=status.HTTP_404_NOT_FOUND)

            if str(wf[0]).upper() != 'MULTI_PERSON':

                return Response({'error': 'Final decision only for MULTI_PERSON workflows'}, status=status.HTTP_400_BAD_REQUEST)



            # Handle overall score override if provided

            if overall_score_override and overall_score_override.get('enabled'):

                try:

                    # Parse request data to get assignment info

                    if isinstance(request_data, str):

                        request_data_obj = json.loads(request_data)

                    else:

                        request_data_obj = request_data

                    

                    rd = request_data_obj.get('request_data', request_data_obj)

                    assignment_id = rd.get('questionnaire_assignment_id')

                    

                    if assignment_id:

                        # Update the assignment with the custom overall score

                        from tprm_backend.apps.vendor_questionnaire.models import QuestionnaireAssignments

                        assignment = QuestionnaireAssignments.objects.get(assignment_id=assignment_id)

                        assignment.overall_score = overall_score_override['custom_score']

                        assignment.save()

                        

                        print(f"Updated assignment {assignment_id} overall score to {overall_score_override['custom_score']}% (override from {overall_score_override.get('original_score', 'unknown')}%)")

                        

                        # Also update the request_data with the new overall score

                        if 'assignment_summary' in rd:

                            rd['assignment_summary']['overall_score'] = float(overall_score_override['custom_score'])

                        

                        # Update the request_data in the database

                        cursor.execute("""

                            UPDATE approval_requests 

                            SET request_data = %s, updated_at = %s 

                            WHERE approval_id = %s

                        """, [json.dumps(request_data_obj), timezone.now(), approval_id])

                        

                except Exception as e:

                    print(f"Error updating overall score override: {str(e)}")

                    # Continue with the decision even if score update fails

            else:

                # Even if no override, ensure the current overall score is saved in request_data

                try:

                    if isinstance(request_data, str):

                        request_data_obj = json.loads(request_data)

                    else:

                        request_data_obj = request_data

                    

                    rd = request_data_obj.get('request_data', request_data_obj)

                    assignment_id = rd.get('questionnaire_assignment_id')

                    

                    if assignment_id:

                        from tprm_backend.apps.vendor_questionnaire.models import QuestionnaireAssignments

                        assignment = QuestionnaireAssignments.objects.get(assignment_id=assignment_id)

                        

                        # Update the assignment_summary with current overall score

                        if 'assignment_summary' in rd:

                            rd['assignment_summary']['overall_score'] = float(assignment.overall_score) if assignment.overall_score else None

                        

                        # Add final decision summary to request_data

                        rd['final_decision_summary'] = {

                            'decision': decision,

                            'reason': reason,

                            'overall_score': float(assignment.overall_score) if assignment.overall_score else None,

                            'decision_made_at': timezone.now().isoformat(),

                            'decision_made_by': user_id,

                            'overall_score_override': overall_score_override

                        }

                        

                        # Update the request_data in the database

                        cursor.execute("""

                            UPDATE approval_requests 

                            SET request_data = %s, updated_at = %s 

                            WHERE approval_id = %s

                        """, [json.dumps(request_data_obj), timezone.now(), approval_id])

                        

                except Exception as e:

                    print(f"Error updating request_data with overall score: {str(e)}")

                    # Continue with the decision even if this update fails



            new_status = 'APPROVED' if decision == 'APPROVE' else 'REJECTED'

            cursor.execute(

                "UPDATE approval_requests SET overall_status=%s, completion_date=%s, updated_at=%s WHERE approval_id=%s",

                [new_status, timezone.now(), timezone.now(), approval_id]

            )

            

            # Create version record for requester final decision (MULTI_PERSON workflow)

            create_approval_version(

                approval_id=approval_id,

                version_type='FINAL',

                version_label=f'Requester Final Decision - {decision}',

                json_payload=request_data,

                changes_summary=f'Requester made final decision: {decision}. Reason: {reason}',

                created_by=user_id,

                created_by_name='Requester',

                created_by_role='Requester',

                change_reason=reason,

                db_connection=db_connection

            )

            

            connections[db_connection].commit()



            # CRITICAL: For MULTI_PERSON response approval, write scores to questionnaire_response_submissions when APPROVED

            if new_status == 'APPROVED' and request_data:

                try:

                    request_data_obj = json.loads(request_data) if isinstance(request_data, str) else request_data

                    rd = request_data_obj.get('request_data', request_data_obj)

                    approval_type = rd.get('approval_type', '').lower().replace(' ', '_')

                    

                    if approval_type == 'response_approval':

                        questionnaire_assignment_id = rd.get('questionnaire_assignment_id')

                        if questionnaire_assignment_id:

                            print(f"Debug - MULTI_PERSON response approval APPROVED, writing scores to database for assignment {questionnaire_assignment_id}")

                            

                            try:

                                from tprm_backend.apps.vendor_questionnaire.models import QuestionnaireAssignments

                                assignment = QuestionnaireAssignments.objects.get(assignment_id=questionnaire_assignment_id)

                                

                                # Get all stages and calculate average scores

                                with connections[db_connection].cursor() as score_cursor:

                                    score_cursor.execute("""

                                        SELECT stage_id, stage_name, assigned_user_name, response_data, stage_status

                                        FROM approval_stages

                                        WHERE approval_id = %s AND stage_status = 'APPROVED'

                                        ORDER BY stage_order

                                    """, [approval_id])

                                    

                                    stages_data = score_cursor.fetchall()

                                    question_averages = {}

                                    

                                    for stage_row in stages_data:

                                        stage_id, stage_name, user_name, stage_response_data, stage_status = stage_row

                                        

                                        if stage_response_data:

                                            try:

                                                if isinstance(stage_response_data, str):

                                                    stage_response = json.loads(stage_response_data)

                                                else:

                                                    stage_response = stage_response_data

                                                

                                                reviewer_scores = stage_response.get('reviewer_scores', {})

                                                

                                                for question_id, score_data in reviewer_scores.items():

                                                    question_id_str = str(question_id)

                                                    score_value = score_data.get('score')

                                                    

                                                    if score_value is not None:

                                                        if question_id_str not in question_averages:

                                                            question_averages[question_id_str] = {

                                                                'scores': [],

                                                                'comments': []

                                                            }

                                                        

                                                        question_averages[question_id_str]['scores'].append(float(score_value))

                                                        question_averages[question_id_str]['comments'].append(score_data.get('comment', ''))

                                                

                                            except Exception as e:

                                                print(f"Error processing stage {stage_id}: {str(e)}")

                                                continue

                                

                                # Write average scores to questionnaire_response_submissions

                                for question_id_str, avg_data in question_averages.items():

                                    if avg_data['scores']:

                                        average_score = sum(avg_data['scores']) / len(avg_data['scores'])

                                        

                                        try:

                                            response = QuestionnaireResponseSubmissions.objects.get(

                                                assignment=assignment,

                                                question_id=int(question_id_str)

                                            )

                                            

                                            response.score = round(average_score, 2)

                                            response.reviewer_comment = '; '.join([c for c in avg_data['comments'] if c.strip()])

                                            response.save()

                                            

                                            print(f"Debug - Written score to DB for Q{question_id_str}: {response.score}")

                                        

                                        except QuestionnaireResponseSubmissions.DoesNotExist:

                                            print(f"Warning - Response not found for question {question_id_str}")

                                            continue

                                        except Exception as e:

                                            print(f"Error updating question {question_id_str}: {str(e)}")

                                            continue

                                

                                print(f"✓ Scores successfully written to questionnaire_response_submissions for assignment {questionnaire_assignment_id}")

                                

                            except Exception as e:

                                print(f"ERROR - Failed to write scores to database: {str(e)}")

                                import traceback

                                traceback.print_exc()

                

                except Exception as e:

                    print(f"ERROR - Failed to process score writing: {str(e)}")



            # Check if this is a final vendor approval and trigger migration for APPROVED status

            if new_status == 'APPROVED' and request_data:

                try:

                    request_data_obj = json.loads(request_data) if isinstance(request_data, str) else request_data

                    rd = request_data_obj.get('request_data', {})

                    approval_type = rd.get('approval_type', '').lower().replace(' ', '_')

                    vendor_id = rd.get('vendor_id')



                    print(f"Debug - Final approval check (multi-person): type={approval_type}, vendor_id={vendor_id}")



                    if approval_type == 'final_vendor_approval' and vendor_id:

                        print(f"Starting vendor migration for final vendor approval: {approval_id}, vendor_id: {vendor_id}")

                        migration_result = migrate_vendor_from_temp_to_main(vendor_id, user_id)

                        print(f"Migration result: {migration_result}")



                        # Add migration info to response

                        if migration_result['success']:

                            migration_info = {

                                'vendor_migration': {

                                    'success': True,

                                    'vendor_id': migration_result['vendor_id'],

                                    'vendor_code': migration_result['vendor_code'],

                                    'company_name': migration_result['company_name'],

                                    'contacts_migrated': migration_result['contacts_migrated'],

                                    'documents_migrated': migration_result['documents_migrated']

                                }

                            }

                        else:

                            migration_info = {

                                'vendor_migration': {

                                    'success': False,

                                    'error': migration_result['error']

                                }

                            }

                except Exception as e:

                    print(f"Error during vendor migration check: {str(e)}")

                    migration_info = {

                        'vendor_migration': {

                            'success': False,

                            'error': f'Migration failed: {str(e)}'

                        }

                    }



            # Update vendor lifecycle stage on final approval

            if new_status == 'APPROVED':

                try:

                    from apps.vendor_core.views import update_temp_vendor_lifecycle_stage, get_lifecycle_stage_id_by_code

                    

                    # Parse request data to get vendor ID if available

                    if request_data:

                        request_data_obj = json.loads(request_data) if isinstance(request_data, str) else request_data

                        rd = request_data_obj.get('request_data', request_data_obj)
                        approval_type = rd.get('approval_type', '').lower().replace(' ', '_')
                        
                        # Try to get vendor_id from multiple sources
                        vendor_id = request_data_obj.get('vendor_id') or rd.get('vendor_id')
                        print(f"Debug - vendor_id from request_data: {vendor_id}, approval_type: {approval_type}")
                        
                        # If not found, try to get from questionnaire_id for questionnaire approval
                        if not vendor_id and approval_type == 'questionnaire_approval':
                            questionnaire_id = rd.get('questionnaire_id')
                            if questionnaire_id:
                                try:
                                    from tprm_backend.apps.vendor_questionnaire.models import Questionnaires
                                    questionnaire = Questionnaires.objects.filter(questionnaire_id=questionnaire_id).first()
                                    if questionnaire and questionnaire.vendor_id:
                                        vendor_id = questionnaire.vendor_id
                                        print(f"Debug - Extracted vendor_id {vendor_id} from questionnaire_id {questionnaire_id}")
                                except Exception as e:
                                    print(f"ERROR - Failed to extract vendor_id from questionnaire: {str(e)}")
                        
                        # If not found, try to get from questionnaire_assignment_id for response approval
                        if not vendor_id and approval_type == 'response_approval':
                            questionnaire_assignment_id = rd.get('questionnaire_assignment_id')
                            if questionnaire_assignment_id:
                                try:
                                    from tprm_backend.apps.vendor_questionnaire.models import QuestionnaireAssignments
                                    assignment = QuestionnaireAssignments.objects.get(assignment_id=questionnaire_assignment_id)
                                    if assignment.temp_vendor:
                                        vendor_id = assignment.temp_vendor.id
                                        print(f"Debug - Extracted vendor_id {vendor_id} from questionnaire_assignment_id {questionnaire_assignment_id}")
                                except Exception as e:
                                    print(f"ERROR - Failed to extract vendor_id from assignment: {str(e)}")

                        print(f"Debug - Final approval decision for vendor {vendor_id}, type: {approval_type}")
                        
                        if vendor_id:
                            # Ensure vendor_id is an integer
                            vendor_id = int(vendor_id) if str(vendor_id).isdigit() else None
                            
                            if vendor_id:
                                if approval_type == 'questionnaire_approval':
                                    # End Questionnaire Approval (Stage 3) and start Questionnaire Response (Stage 4)
                                    print(f"Initiating Lifecycle Stage 3 (Questionnaire Approval) completion for vendor {vendor_id}")
                                    _end_questionnaire_approval_start_questionnaire_response(vendor_id)
                                    print(f"✓ Lifecycle Stage 3 (Questionnaire Approval) completed for vendor {vendor_id}")
                                elif approval_type == 'response_approval':
                                    # End Response Approval and start Vendor Approval
                                    print(f"Initiating Response Approval completion for vendor {vendor_id}")
                                    _end_response_approval_start_vendor_approval(vendor_id)
                                    print(f"✓ Response Approval lifecycle stage completed for vendor {vendor_id}")
                                elif approval_type == 'vendor_approval' or approval_type == 'final_vendor_approval':
                                    # End Vendor Approval stage (final completion)
                                    print(f"Initiating Vendor Approval completion for vendor {vendor_id}")
                                    _end_vendor_approval_stage(vendor_id)
                                    print(f"✓ Vendor Approval lifecycle stage completed for vendor {vendor_id}")
                                else:
                                    print(f"Unknown approval type: {approval_type} for vendor {vendor_id}")
                            else:
                                print(f"WARNING - vendor_id could not be converted to integer: {vendor_id}")
                        else:
                            print(f"WARNING - Could not extract vendor_id for lifecycle tracking. Approval type: {approval_type}")
                            print(f"DEBUG - request_data: {request_data_obj}")
                except Exception as e:
                    # Don't fail the approval process if lifecycle stage update fails
                    print(f"ERROR - Failed to update vendor lifecycle stage on final approval: {str(e)}")
                    import traceback
                    traceback.print_exc()



            # Trigger vendor risk generation for approved response assessments

            if new_status == 'APPROVED':

                try:

                    # Check if this is a response approval workflow

                    if isinstance(request_data, str):

                        request_data_obj = json.loads(request_data)

                    else:

                        request_data_obj = request_data

                    

                    rd = request_data_obj.get('request_data', request_data_obj)

                    approval_type = rd.get('approval_type', '').lower().replace(' ', '_')

                    

                    # Only trigger for response approval workflows

                    if approval_type == 'response_approval':

                        print(f"Triggering vendor risk generation for approved response assessment: {approval_id}")

                        

                        # Import and trigger the threading-based async risk generation
                        import logging
                        import traceback
                        logger = logging.getLogger(__name__)
                        
                        try:
                            from tprm_backend.risk_analysis_vendor.services import RiskAnalysisService
                            logger.info(f"✅ [RISK GENERATION] Successfully imported RiskAnalysisService")
                            print(f"✅ [RISK GENERATION] Successfully imported RiskAnalysisService")
                        except ImportError as import_error:
                            logger.error(f"❌ [RISK GENERATION] Failed to import RiskAnalysisService: {str(import_error)}")
                            print(f"❌ [RISK GENERATION] Failed to import RiskAnalysisService: {str(import_error)}")
                            print(f"❌ [RISK GENERATION] Import traceback: {traceback.format_exc()}")
                            raise

                        

                        try:
                            risk_service = RiskAnalysisService()
                            logger.info(f"✅ [RISK GENERATION] Created RiskAnalysisService instance")
                            print(f"✅ [RISK GENERATION] Created RiskAnalysisService instance")
                            
                            result = risk_service.generate_vendor_risks_async(approval_id)
                            logger.info(f"✅ [RISK GENERATION] Called generate_vendor_risks_async, result: {result}")
                            print(f"✅ [RISK GENERATION] Vendor risk generation started in background thread: {result}")
                            
                            if result.get('status') == 'error':
                                logger.error(f"❌ [RISK GENERATION] Error in risk generation result: {result.get('error')}")
                                print(f"❌ [RISK GENERATION] Error in risk generation result: {result.get('error')}")
                            else:
                                logger.info(f"✅ [RISK GENERATION] Risk generation successfully initiated")
                                print(f"✅ [RISK GENERATION] Risk generation successfully initiated")
                                
                        except Exception as service_error:
                            logger.error(f"❌ [RISK GENERATION] Error calling RiskAnalysisService: {str(service_error)}")
                            logger.error(f"❌ [RISK GENERATION] Service error traceback: {traceback.format_exc()}")
                            print(f"❌ [RISK GENERATION] Error calling RiskAnalysisService: {str(service_error)}")
                            print(f"❌ [RISK GENERATION] Service error traceback: {traceback.format_exc()}")
                            raise

                        
                        # Initialize migration_info if it doesn't exist
                        if 'migration_info' not in locals():
                            migration_info = {}
                        
                        # Store the risk generation task info for status checking
                        migration_info['risk_generation'] = {
                            'status': result.get('status', 'started'),
                            'approval_id': approval_id,
                            'thread_name': result.get('thread_name', 'unknown'),
                            'message': result.get('message', 'Risk generation started'),
                            'error': result.get('error') if result.get('status') == 'error' else None
                        }

                    

                except Exception as e:

                    # Log error but don't fail the approval process
                    import logging
                    import traceback
                    logger = logging.getLogger(__name__)
                    
                    error_trace = traceback.format_exc()
                    logger.error(f"❌ [RISK GENERATION] Error triggering vendor risk generation for approval {approval_id}: {str(e)}")
                    logger.error(f"❌ [RISK GENERATION] Full traceback: {error_trace}")
                    print(f"❌ [RISK GENERATION] Error triggering vendor risk generation for approval {approval_id}: {str(e)}")
                    print(f"❌ [RISK GENERATION] Full traceback: {error_trace}")



            # Return success response

            response_data = {

                'success': True,

                'message': f'Final decision {decision} submitted successfully',

                'approval_id': approval_id,

                'new_status': new_status,

                'decision': decision,

                'reason': reason

            }

            

            # Add migration info if available

            if 'migration_info' in locals():

                response_data.update(migration_info)

            

            return Response(response_data, status=status.HTTP_200_OK)



    except Exception as e:

        print(f"Error saving requester final decision: {str(e)}")

        return Response({'error': 'Failed to save final decision', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('approve_reject_vendor')
@require_tenant
@tenant_filter
def admin_handle_rejection(request, approval_id):

    """Admin endpoint to handle rejected workflows in MULTI_LEVEL workflows.
    MULTI-TENANCY: Ensures approval belongs to tenant's vendor

    Payload: { 

        action: 'RESTART_FROM_REJECTED' | 'RESTART_FROM_STAGE' | 'FINAL_REJECT',

        stage_order?: int (for RESTART_FROM_STAGE),

        admin_comments?: str,

        admin_id: str,

        admin_name: str

    }

    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        data = request.data or {}

        action = data.get('action', '').upper()

        admin_comments = data.get('admin_comments', '')
        
        # Get user ID and username - use authenticated user if available, otherwise default
        if hasattr(request, 'user') and request.user.is_authenticated:
            admin_id = request.user.id
            admin_name = request.user.username
        print(f"🔍 Admin user info: ID={admin_id}, Name={admin_name}")

        

        if action not in ('RESTART_FROM_REJECTED', 'RESTART_FROM_STAGE', 'FINAL_REJECT'):

            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)



        with connections['default'].cursor() as cursor:

            # Get workflow details

            cursor.execute("""

                SELECT ar.workflow_id, ar.overall_status, aw.workflow_type, ar.request_data

                FROM approval_requests ar

                JOIN approval_workflows aw ON ar.workflow_id = aw.workflow_id

                WHERE ar.approval_id = %s

            """, [approval_id])

            

            request_row = cursor.fetchone()

            if not request_row:

                return Response({'error': 'Approval request not found'}, status=status.HTTP_404_NOT_FOUND)

            

            workflow_id, overall_status, workflow_type, request_data = request_row

            

            if workflow_type != 'MULTI_LEVEL':

                return Response({'error': 'Admin rejection handling only for MULTI_LEVEL workflows'}, status=status.HTTP_400_BAD_REQUEST)

            

            now_ts = timezone.now()

            

            if action == 'RESTART_FROM_REJECTED':

                # Find the rejected stage and restart from there

                cursor.execute("""

                    SELECT stage_id, stage_order, stage_name 

                    FROM approval_stages 

                    WHERE approval_id = %s AND stage_status = 'REJECTED'

                    ORDER BY stage_order ASC

                    LIMIT 1

                """, [approval_id])

                

                rejected_stage_row = cursor.fetchone()

                if not rejected_stage_row:

                    return Response({'error': 'No rejected stage found'}, status=status.HTTP_404_NOT_FOUND)

                

                rejected_stage_id, rejected_stage_order, rejected_stage_name = rejected_stage_row

                

                # Reset stages from rejected stage onwards

                cursor.execute("""

                    UPDATE approval_stages 

                    SET stage_status='PENDING', completed_at=NULL, response_data=NULL, 

                        rejection_reason=NULL, started_at=NULL

                    WHERE approval_id = %s AND stage_order >= %s

                """, [approval_id, rejected_stage_order])

                

                # Set rejected stage to IN_PROGRESS

                cursor.execute("""

                    UPDATE approval_stages 

                    SET stage_status='IN_PROGRESS', started_at=%s

                    WHERE stage_id = %s

                """, [now_ts, rejected_stage_id])

                

                # Update overall request status

                cursor.execute("""

                    UPDATE approval_requests 

                    SET overall_status='IN_PROGRESS', updated_at=%s 

                    WHERE approval_id=%s

                """, [now_ts, approval_id])

                

                # Create version record
                print(f"\n{'='*80}")
                print(f"🔄 CREATING VERSION for Admin Action: RESTART_FROM_REJECTED")
                print(f"{'='*80}")
                print(f"📝 Approval ID: {approval_id}")
                print(f"📝 Stage: {rejected_stage_name}")
                print(f"📝 Admin: {admin_name} (ID: {admin_id})")
                print(f"🚀 Calling create_approval_version()...")
                
                version_id = create_approval_version(

                    approval_id=approval_id,

                    version_type='REVISION',

                    version_label=f'Admin Restart from Stage {rejected_stage_name}',

                    json_payload=request_data,

                    changes_summary=f'Admin restarted workflow from rejected stage: {rejected_stage_name}. {admin_comments}',

                    created_by=admin_id,

                    created_by_name=admin_name,

                    created_by_role='Administrator',

                    change_reason=admin_comments

                )
                
                if version_id:
                    print(f"✅ SUCCESS! Version created: {version_id}")
                    print(f"✅ Admin action 'RESTART_FROM_REJECTED' recorded in version table")
                else:
                    print(f"❌ FAILURE - create_approval_version returned None")
                    print(f"❌ Admin action was NOT recorded in version table!")
                print(f"{'='*80}\n")

                

                message = f'Workflow restarted from rejected stage: {rejected_stage_name}'

                

            elif action == 'RESTART_FROM_STAGE':

                target_stage_order = data.get('stage_order')

                if not target_stage_order:

                    return Response({'error': 'stage_order required for RESTART_FROM_STAGE'}, status=status.HTTP_400_BAD_REQUEST)

                

                # Get target stage details

                cursor.execute("""

                    SELECT stage_id, stage_name 

                    FROM approval_stages 

                    WHERE approval_id = %s AND stage_order = %s

                """, [approval_id, target_stage_order])

                

                target_stage_row = cursor.fetchone()

                if not target_stage_row:

                    return Response({'error': 'Target stage not found'}, status=status.HTTP_404_NOT_FOUND)

                

                target_stage_id, target_stage_name = target_stage_row

                

                # Reset stages from target stage onwards

                cursor.execute("""

                    UPDATE approval_stages 

                    SET stage_status='PENDING', completed_at=NULL, response_data=NULL, 

                        rejection_reason=NULL, started_at=NULL

                    WHERE approval_id = %s AND stage_order >= %s

                """, [approval_id, target_stage_order])

                

                # Set target stage to IN_PROGRESS

                cursor.execute("""

                    UPDATE approval_stages 

                    SET stage_status='IN_PROGRESS', started_at=%s

                    WHERE stage_id = %s

                """, [now_ts, target_stage_id])

                

                # Update overall request status

                cursor.execute("""

                    UPDATE approval_requests 

                    SET overall_status='IN_PROGRESS', updated_at=%s 

                    WHERE approval_id=%s

                """, [now_ts, approval_id])

                

                # Create version record
                print(f"\n{'='*80}")
                print(f"🔄 CREATING VERSION for Admin Action: RESTART_FROM_STAGE")
                print(f"{'='*80}")
                print(f"📝 Approval ID: {approval_id}")
                print(f"📝 Stage: {target_stage_name} (Order: {target_stage_order})")
                print(f"📝 Admin: {admin_name} (ID: {admin_id})")
                print(f"🚀 Calling create_approval_version()...")
                
                version_id = create_approval_version(

                    approval_id=approval_id,

                    version_type='REVISION',

                    version_label=f'Admin Restart from Stage {target_stage_name}',

                    json_payload=request_data,

                    changes_summary=f'Admin restarted workflow from stage {target_stage_order}: {target_stage_name}. {admin_comments}',

                    created_by=admin_id,

                    created_by_name=admin_name,

                    created_by_role='Administrator',

                    change_reason=admin_comments

                )
                
                if version_id:
                    print(f"✅ SUCCESS! Version created: {version_id}")
                    print(f"✅ Admin action 'RESTART_FROM_STAGE' recorded in version table")
                else:
                    print(f"❌ FAILURE - create_approval_version returned None")
                    print(f"❌ Admin action was NOT recorded in version table!")
                print(f"{'='*80}\n")

                

                message = f'Workflow restarted from stage {target_stage_order}: {target_stage_name}'

                

            elif action == 'FINAL_REJECT':

                # Final rejection by admin

                cursor.execute("""

                    UPDATE approval_requests 

                    SET overall_status='REJECTED', completion_date=%s, updated_at=%s 

                    WHERE approval_id=%s

                """, [now_ts, now_ts, approval_id])

                

                # Create final version record
                print(f"\n{'='*80}")
                print(f"🔄 CREATING VERSION for Admin Action: FINAL_REJECT")
                print(f"{'='*80}")
                print(f"📝 Approval ID: {approval_id}")
                print(f"📝 Admin: {admin_name} (ID: {admin_id})")
                print(f"📝 Comments: {admin_comments}")
                print(f"🚀 Calling create_approval_version()...")
                
                version_id = create_approval_version(

                    approval_id=approval_id,

                    version_type='FINAL',

                    version_label='Admin Final Rejection',

                    json_payload=request_data,

                    changes_summary=f'Admin final rejection: {admin_comments}',

                    created_by=admin_id,

                    created_by_name=admin_name,

                    created_by_role='Administrator',

                    change_reason=admin_comments

                )
                
                if version_id:
                    print(f"✅ SUCCESS! Version created: {version_id}")
                    print(f"✅ Admin action 'FINAL_REJECT' recorded in version table")
                else:
                    print(f"❌ FAILURE - create_approval_version returned None")
                    print(f"❌ Admin action was NOT recorded in version table!")
                print(f"{'='*80}\n")

                

                message = 'Workflow finally rejected by administrator'



        connection.commit()

        return Response({'message': message}, status=status.HTTP_200_OK)

        

    except Exception as e:

        print(f"Error handling admin rejection: {str(e)}")

        return Response({

            'error': 'Failed to handle admin rejection',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_request_versions(request, approval_id):

    """Get version history for an approval request
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        # Use tprm database connection where temp_vendor table exists
        db_connection = 'tprm'
        try:
            if 'tprm' not in connections.databases:
                db_connection = 'default'
        except Exception as db_check_error:
            print(f"Warning: Error checking database connections: {db_check_error}, using 'tprm' connection")

        with connections[db_connection].cursor() as cursor:
            # MULTI-TENANCY: Filter by tenant through approval request
            cursor.execute("""

                SELECT arv.version_id, arv.version_number, arv.version_label, arv.changes_summary, 

                       arv.created_by, arv.created_by_name, arv.created_by_role, arv.version_type, 

                       arv.parent_version_id, arv.is_current, arv.is_approved, arv.change_reason, arv.created_at

                FROM approval_request_versions arv

                JOIN approval_requests ar ON arv.approval_id = ar.approval_id
                
                LEFT JOIN temp_vendor tv ON JSON_EXTRACT(ar.request_data, '$.vendor_id') = tv.id

                WHERE arv.approval_id = %s 
                
                AND (tv.TenantId = %s OR tv.TenantId IS NULL)

                ORDER BY arv.version_number DESC

            """, [approval_id, tenant_id])

            

            versions = cursor.fetchall()

            

            versions_list = []

            for version in versions:

                versions_list.append({

                    'version_id': version[0],

                    'version_number': version[1],

                    'version_label': version[2],

                    'changes_summary': version[3],

                    'created_by': version[4],

                    'created_by_name': version[5],

                    'created_by_role': version[6],

                    'version_type': version[7],

                    'parent_version_id': version[8],

                    'is_current': bool(version[9]),

                    'is_approved': bool(version[10]),

                    'change_reason': version[11],

                    'created_at': version[12].isoformat() if version[12] else None

                })

            

            return Response(versions_list, status=status.HTTP_200_OK)

            

    except Exception as e:

        print(f"Error fetching request versions: {str(e)}")

        return Response({

            'error': 'Failed to fetch request versions',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
def debug_version_data(request, approval_id):
    """
    Debug endpoint to display detailed version data for a specific approval request.
    Use this to verify version creation and data integrity.
    """
    try:
        with connections['default'].cursor() as cursor:
            # Get all versions with full details
            cursor.execute("""
                SELECT 
                    version_id, 
                    approval_id,
                    version_number, 
                    version_label, 
                    changes_summary, 
                    created_by, 
                    created_by_name, 
                    created_by_role, 
                    version_type, 
                    parent_version_id, 
                    is_current, 
                    is_approved, 
                    change_reason, 
                    created_at,
                    json_payload
                FROM approval_request_versions 
                WHERE approval_id = %s 
                ORDER BY version_number DESC
            """, [approval_id])
            
            versions = cursor.fetchall()
            
            if not versions:
                return Response({
                    'message': f'No versions found for approval_id: {approval_id}',
                    'total_versions': 0
                }, status=status.HTTP_200_OK)
            
            # Format response with detailed information
            versions_list = []
            for v in versions:
                version_data = {
                    'version_id': v[0],
                    'approval_id': v[1],
                    'version_number': v[2],
                    'version_label': v[3],
                    'changes_summary': v[4],
                    'created_by': v[5],
                    'created_by_name': v[6],
                    'created_by_role': v[7],
                    'version_type': v[8],
                    'parent_version_id': v[9],
                    'is_current': bool(v[10]),
                    'is_approved': bool(v[11]),
                    'change_reason': v[12],
                    'created_at': v[13].isoformat() if v[13] else None,
                    'has_json_payload': v[14] is not None
                }
                versions_list.append(version_data)
            
            # Add summary statistics
            current_version = next((v for v in versions_list if v['is_current']), None)
            
            response_data = {
                'approval_id': approval_id,
                'total_versions': len(versions_list),
                'current_version_number': current_version['version_number'] if current_version else None,
                'current_version_label': current_version['version_label'] if current_version else None,
                'versions': versions_list,
                'version_types': {
                    vtype: len([v for v in versions_list if v['version_type'] == vtype])
                    for vtype in set(v['version_type'] for v in versions_list)
                }
            }
            
            print(f"\n{'='*80}")
            print(f"DEBUG VERSION DATA FOR APPROVAL: {approval_id}")
            print(f"{'='*80}")
            print(f"Total Versions: {len(versions_list)}")
            print(f"Current Version: v{current_version['version_number']} - {current_version['version_label']}" if current_version else "No current version")
            print(f"\nVersion Breakdown:")
            for v in versions_list:
                status_icon = "→" if v['is_current'] else " "
                print(f"  {status_icon} v{v['version_number']:2d} | {v['version_type']:10s} | {v['version_label']}")
                print(f"     Created by: {v['created_by_name']} ({v['created_by_role']}) at {v['created_at']}")
                if v['changes_summary']:
                    print(f"     Changes: {v['changes_summary']}")
                if v['change_reason']:
                    print(f"     Reason: {v['change_reason']}")
                print()
            print(f"{'='*80}\n")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
    except Exception as e:
        print(f"Error in debug_version_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': 'Failed to fetch version data',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('create_vendor')
@require_tenant
@tenant_filter
def create_workflow(request):

    """Create a new approval workflow with stages
    MULTI-TENANCY: Workflows are created in tenant context
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        data = request.data

        

        # Validate required fields

        if not data.get('workflow_name'):

            return Response({

                'error': 'Workflow name is required'

            }, status=status.HTTP_400_BAD_REQUEST)

        

        if not data.get('stages_config') or len(data.get('stages_config', [])) == 0:

            return Response({

                'error': 'At least one stage is required'

            }, status=status.HTTP_400_BAD_REQUEST)

        

        try:

            with connections['default'].cursor() as cursor:

                # Temporarily disable foreign key checks

                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

                
                # Get logged-in user information for assignee data
                logged_in_user_id = int(data.get('created_by')) if str(data.get('created_by')).isdigit() else request.session.get('user_id', 1)
                
                # Query users table to get user name and role
                # Users table is typically in default database
                user_row = None
                try:
                    cursor.execute("""
                        SELECT UserId, UserName, Email 
                        FROM users 
                        WHERE UserId = %s
                        LIMIT 1
                    """, [logged_in_user_id])
                    user_row = cursor.fetchone()
                except Exception as e:
                    # If users table doesn't exist in current connection, try default
                    try:
                        with connections['default'].cursor() as default_cursor:
                            default_cursor.execute("""
                                SELECT UserId, UserName, Email 
                                FROM users 
                                WHERE UserId = %s
                                LIMIT 1
                            """, [logged_in_user_id])
                            user_row = default_cursor.fetchone()
                    except:
                        pass
                
                if user_row:
                    logged_in_user_name = user_row[1] if user_row[1] else f'User {logged_in_user_id}'
                    logged_in_user_role = 'Manager'  # Default role, can be enhanced later
                else:
                    logged_in_user_name = f'User {logged_in_user_id}'
                    logged_in_user_role = 'Manager'

                # 1. Create workflow

                workflow_id = str(uuid.uuid4()).replace('-', '').upper()[:16]

                cursor.execute("""
                    INSERT INTO approval_workflows 
                    (workflow_id, workflow_name, workflow_type, description, business_object_type, 
                     TenantId, is_active, created_by, created_at, updated_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    workflow_id,
                    data.get('workflow_name', ''),
                    data.get('workflow_type', 'MULTI_LEVEL'),
                    data.get('description', ''),
                    data.get('business_object_type', ''),
                    tenant_id,
                    True,
                    logged_in_user_id,
                    timezone.now(),
                    timezone.now()
                ])

                

                # 2. Create stages configuration (store as JSON in workflow)

                stages_config = data.get('stages_config', [])

                

                # Process stages and create stage records

                for stage_config in stages_config:

                    stage_id = str(uuid.uuid4()).replace('-', '').upper()[:16]

                    

                    # Convert deadline_date string to timestamp if needed

                    deadline_date = stage_config.get('deadline_date')

                    if deadline_date and isinstance(deadline_date, str):

                        try:

                            from datetime import datetime

                            deadline_date = datetime.fromisoformat(deadline_date.replace('Z', '+00:00'))

                        except:

                            deadline_date = timezone.now()

                    

                    # Insert stage configuration

                    # Initialize response_data for each stage

                    initial_response_data = standardize_response_data(

                        response_data={},

                        stage_status='PENDING',

                        decision='',

                        comments='',

                        rejection_reason=''

                    )

                    

                    cursor.execute("""

                        INSERT INTO approval_stages 

                        (stage_id, approval_id, stage_order, stage_name, stage_description, 

                         assigned_user_id, assigned_user_name, assigned_user_role, department, 

                         stage_type, stage_status, deadline_date, response_data, is_mandatory, TenantId, created_at, updated_at) 

                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

                    """, [

                        stage_id,

                        None,  # No approval request yet

                        stage_config.get('stage_order', 1),

                        stage_config.get('stage_name', ''),

                        stage_config.get('stage_description', ''),

                        stage_config.get('assigned_user_id'),  # Use selected user from dropdown

                        stage_config.get('assigned_user_name', ''),  # Use selected user name from dropdown

                        stage_config.get('assigned_user_role', ''),  # Use selected user role from dropdown

                        stage_config.get('department', ''),

                        stage_config.get('stage_type', 'SEQUENTIAL'),

                        'PENDING',

                        deadline_date or timezone.now(),

                        json.dumps(initial_response_data),

                        stage_config.get('is_mandatory', True),

                        tenant_id,

                        timezone.now(),

                        timezone.now()

                    ])

                

                # Re-enable foreign key checks

                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

                connection.commit()

                

                print(f"Created workflow: {workflow_id}")

                

                return Response({

                    'workflow_id': workflow_id,

                    'message': 'Workflow created successfully',

                    'stages_count': len(stages_config)

                }, status=status.HTTP_201_CREATED)

                

        except Exception as e:

            print(f"Database error: {str(e)}")

            return Response({

                'error': 'Failed to create workflow in database',

                'details': str(e)

            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            

    except Exception as e:

        print(f"General error: {str(e)}")

        return Response({

            'error': 'Failed to process workflow creation request',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_workflows(request):

    """Get all approval workflows
    MULTI-TENANCY: Workflows may be shared across tenants for Vendor business_object_type
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        with connections['default'].cursor() as cursor:

            cursor.execute("""

                SELECT workflow_id, workflow_name, workflow_type, description, 

                       business_object_type, is_active, created_by, created_at, updated_at

                FROM approval_workflows 

                ORDER BY created_at DESC

            """)

            columns = [col[0] for col in cursor.description]

            workflows = [dict(zip(columns, row)) for row in cursor.fetchall()]

            

            return Response(workflows, status=status.HTTP_200_OK)

            

    except Exception as e:

        print(f"Error fetching workflows: {str(e)}")

        return Response({

            'error': 'Failed to fetch workflows',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_workflow_stages(request, workflow_id):

    """Get stages for a specific workflow
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        with connections['default'].cursor() as cursor:

            cursor.execute("""

                SELECT stage_id, stage_order, stage_name, stage_description, 

                       assigned_user_id, assigned_user_name, assigned_user_role, 

                       department, stage_type, stage_status, deadline_date, is_mandatory

                FROM approval_stages 

                WHERE approval_id IS NULL

                ORDER BY stage_order

            """)

            columns = [col[0] for col in cursor.description]

            stages = [dict(zip(columns, row)) for row in cursor.fetchall()]

            

            return Response(stages, status=status.HTTP_200_OK)

            

    except Exception as e:

        print(f"Error fetching workflow stages: {str(e)}")

        return Response({

            'error': 'Failed to fetch workflow stages',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('SubmitVendorForApproval')
@require_tenant
@tenant_filter
def create_workflow_request(request):

    """Create an approval request using an existing workflow
    MULTI-TENANCY: Ensures vendor belongs to tenant
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        data = request.data

        

        # Validate required fields

        if not data.get('workflow_id'):

            return Response({

                'error': 'Workflow ID is required'

            }, status=status.HTTP_400_BAD_REQUEST)

        

        if not data.get('request_title'):

            return Response({

                'error': 'Request title is required'

            }, status=status.HTTP_400_BAD_REQUEST)

        

        try:

            with connections['default'].cursor() as cursor:

                # Temporarily disable foreign key checks

                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

                
                # Get logged-in user information for assignee data
                logged_in_user_id = int(data.get('requester_id')) if str(data.get('requester_id')).isdigit() else request.session.get('user_id', 1)
                
                # Query users table to get user name and role
                # Users table is typically in default database
                user_row = None
                try:
                    cursor.execute("""
                        SELECT UserId, UserName, Email 
                        FROM users 
                        WHERE UserId = %s
                        LIMIT 1
                    """, [logged_in_user_id])
                    user_row = cursor.fetchone()
                except Exception as e:
                    # If users table doesn't exist in current connection, try default
                    try:
                        with connections['default'].cursor() as default_cursor:
                            default_cursor.execute("""
                                SELECT UserId, UserName, Email 
                                FROM users 
                                WHERE UserId = %s
                                LIMIT 1
                            """, [logged_in_user_id])
                            user_row = default_cursor.fetchone()
                    except:
                        pass
                
                if user_row:
                    logged_in_user_name = user_row[1] if user_row[1] else f'User {logged_in_user_id}'
                    logged_in_user_role = 'Manager'  # Default role, can be enhanced later
                else:
                    logged_in_user_name = f'User {logged_in_user_id}'
                    logged_in_user_role = 'Manager'

                # 1. Create approval request

                approval_id = str(uuid.uuid4()).replace('-', '').upper()[:16]

                cursor.execute("""

                    INSERT INTO approval_requests 
                    (approval_id, workflow_id, request_title, request_description, requester_id, 
                     requester_department, priority, request_data, overall_status, 
                     submission_date, created_at, updated_at, TenantId) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

                """, [

                    approval_id,

                    data.get('workflow_id'),

                    data.get('request_title', ''),

                    data.get('request_description', ''),

                    data.get('requester_id', 'Current User'),

                    data.get('requester_department', ''),

                    data.get('priority', 'MEDIUM'),

                    json.dumps(data.get('request_data', {})),
                    'PENDING',
                    timezone.now(),
                    timezone.now(),
                    timezone.now(),
                    tenant_id

                ])

                

                # 2. Copy workflow stages to approval stages

                cursor.execute("""

                    SELECT stage_order, stage_name, stage_description, 

                           assigned_user_id, assigned_user_name, assigned_user_role, 

                           department, stage_type, deadline_date, is_mandatory

                    FROM approval_stages 

                    WHERE approval_id IS NULL

                    ORDER BY stage_order

                """)

                

                workflow_stages = cursor.fetchall()

                

                for stage_data in workflow_stages:

                    stage_id = str(uuid.uuid4()).replace('-', '').upper()[:16]

                    

                    # Initialize response_data for each stage

                    initial_response_data = standardize_response_data(

                        response_data={},

                        stage_status='PENDING',

                        decision='',

                        comments='',

                        rejection_reason=''

                    )

                    

                    cursor.execute("""

                        INSERT INTO approval_stages 

                        (stage_id, approval_id, stage_order, stage_name, stage_description, 

                         assigned_user_id, assigned_user_name, assigned_user_role, department, 

                         stage_type, stage_status, deadline_date, response_data, is_mandatory, TenantId, created_at, updated_at) 

                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

                    """, [

                        stage_id,

                        approval_id,

                        stage_data[0],  # stage_order

                        stage_data[1],  # stage_name

                        stage_data[2],  # stage_description

                        stage_data[3],  # assigned_user_id (from workflow stage)

                        stage_data[4],  # assigned_user_name (from workflow stage)

                        stage_data[5],  # assigned_user_role (from workflow stage)

                        stage_data[6],  # department

                        stage_data[7],  # stage_type

                        'PENDING',

                        stage_data[8],  # deadline_date

                        json.dumps(initial_response_data),

                        stage_data[9],  # is_mandatory

                        tenant_id,

                        timezone.now(),

                        timezone.now()

                    ])

                

                # Re-enable foreign key checks

                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

                connection.commit()

                

                print(f"Created approval request: {approval_id}")

                

                return Response({

                    'approval_id': approval_id,

                    'message': 'Approval request created successfully'

                }, status=status.HTTP_201_CREATED)

                

        except Exception as e:

            print(f"Database error: {str(e)}")

            return Response({

                'error': 'Failed to create approval request in database',

                'details': str(e)

            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            

    except Exception as e:

        print(f"General error: {str(e)}")

        return Response({

            'error': 'Failed to process approval request creation',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('SubmitVendorForApproval')
@require_tenant
@tenant_filter
def create_comprehensive_workflow(request):

    """Create a comprehensive workflow with request and stages in one operation
    MULTI-TENANCY: Ensures vendor belongs to tenant
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        data = request.data

        

        # Extract data for each component

        workflow_data = data.get('workflow', {})

        request_data = data.get('request', {})

        stages_data = data.get('stages', [])

        

        # Validate required data

        if not workflow_data.get('workflow_name'):

            return Response({

                'error': 'Workflow name is required'

            }, status=status.HTTP_400_BAD_REQUEST)

        

        if not request_data.get('request_title'):

            return Response({

                'error': 'Request title is required'

            }, status=status.HTTP_400_BAD_REQUEST)

        

        if not stages_data:

            return Response({

                'error': 'At least one stage is required'

            }, status=status.HTTP_400_BAD_REQUEST)

        

        try:
            # Use tprm database connection for vendor approval queries
            # This ensures data is written to the same database where it's read from
            db_connection = 'tprm'
            try:
                # Check if 'tprm' connection exists
                if 'tprm' not in connections.databases:
                    print("Warning: 'tprm' database connection not found, falling back to 'default'")
                    db_connection = 'default'
                else:
                    print(f"Using 'tprm' database connection for workflow creation (tprm_integration)")
            except Exception as db_check_error:
                print(f"Warning: Error checking database connections: {db_check_error}, using 'tprm' connection")

            with connections[db_connection].cursor() as cursor:

                # Temporarily disable foreign key checks

                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

                
                # Get logged-in user information for assignee data
                logged_in_user_id = int(request_data.get('requester_id')) if str(request_data.get('requester_id')).isdigit() else request.session.get('user_id', 1)
                
                # Query users table to get user name and role
                # Try current connection first, then fall back to default if users table doesn't exist
                user_row = None
                try:
                    cursor.execute("""
                        SELECT UserId, UserName, Email 
                        FROM users 
                        WHERE UserId = %s
                        LIMIT 1
                    """, [logged_in_user_id])
                    user_row = cursor.fetchone()
                except Exception as e:
                    # If users table doesn't exist in current connection, try default
                    try:
                        with connections['default'].cursor() as default_cursor:
                            default_cursor.execute("""
                                SELECT UserId, UserName, Email 
                                FROM users 
                                WHERE UserId = %s
                                LIMIT 1
                            """, [logged_in_user_id])
                            user_row = default_cursor.fetchone()
                    except:
                        pass
                
                if user_row:
                    logged_in_user_name = user_row[1] if user_row[1] else f'User {logged_in_user_id}'
                    logged_in_user_role = 'Manager'  # Default role, can be enhanced later
                else:
                    logged_in_user_name = f'User {logged_in_user_id}'
                    logged_in_user_role = 'Manager'

                # 1. Create workflow

                workflow_id = str(uuid.uuid4()).replace('-', '').upper()[:16]

                cursor.execute("""
                    INSERT INTO approval_workflows 
                    (workflow_id, workflow_name, workflow_type, description, business_object_type, 
                     TenantId, is_active, created_by, created_at, updated_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    workflow_id,
                    workflow_data.get('workflow_name', ''),
                    workflow_data.get('workflow_type', 'MULTI_LEVEL'),
                    workflow_data.get('description', ''),
                    workflow_data.get('business_object_type', 'Vendor'),
                    tenant_id,
                    True,
                    logged_in_user_id,
                    timezone.now(),
                    timezone.now()
                ])

                

                # 2. Create approval request

                approval_id = str(uuid.uuid4()).replace('-', '').upper()[:16]

                # Note: approval_requests table does not have business_object_type/business_object_id

                cursor.execute("""
                    INSERT INTO approval_requests 
                    (approval_id, workflow_id, request_title, request_description, requester_id, 
                     requester_department, priority, request_data, overall_status, 
                     submission_date, created_at, updated_at, TenantId) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    approval_id,
                    workflow_id,
                    request_data.get('request_title', ''),
                    request_data.get('request_description', ''),
                    int(request_data.get('requester_id')) if str(request_data.get('requester_id')).isdigit() else request.session.get('user_id', 1),
                    request_data.get('requester_department', ''),
                    request_data.get('priority', 'MEDIUM'),
                    json.dumps(request_data),  # store entire request payload
                    'PENDING',
                    timezone.now(),
                    timezone.now(),
                    timezone.now(),
                    tenant_id
                ])

                

                # 3. Create stages
                print(f"Debug - Creating {len(stages_data)} stages...")
                for i, stage_config in enumerate(stages_data):
                    print(f"Debug - Stage {i+1}: {stage_config}")

                    stage_id = str(uuid.uuid4()).replace('-', '').upper()[:16]

                    

                    # Convert deadline_date string to timestamp if needed

                    deadline_date = stage_config.get('deadline_date')

                    if deadline_date and isinstance(deadline_date, str):

                        try:

                            from datetime import datetime

                            deadline_date = datetime.fromisoformat(deadline_date.replace('Z', '+00:00'))

                        except:

                            deadline_date = timezone.now()

                    

                    # Determine initial stage status based on workflow type

                    initial_stage_status =  'PENDING'
                    started_at = None

                    if workflow_data.get('workflow_type') == 'MULTI_LEVEL' and stage_config.get('stage_order', 1) == 1:

                        # First stage of sequential workflow should be active

                        initial_stage_status = 'IN_PROGRESS'
                        started_at = timezone.now()

                    elif workflow_data.get('workflow_type') == 'MULTI_PERSON':

                        # All stages of parallel workflow should be active

                        initial_stage_status = 'IN_PROGRESS'
                        started_at = timezone.now()
                    
                    # Special handling for Questionnaire Approval stage (Lifecycle Stage 3)
                    print(f"Debug - Checking stage: {stage_config.get('stage_name', '')} - Status: {initial_stage_status}")
                    
                    # Check approval_type from request data instead of stage name
                    approval_type = None
                    if isinstance(request_data, dict):
                        approval_type = request_data.get('approval_type', '')
                        if not approval_type:
                            nested_request_data = request_data.get('request_data', {})
                            if isinstance(nested_request_data, dict):
                                approval_type = nested_request_data.get('approval_type', '')
                    
                    # If no approval_type found, try to infer from workflow data or stage name
                    if not approval_type:
                        # Check if this is a questionnaire-related workflow
                        workflow_name = workflow_data.get('workflow_name', '') if workflow_data else ''
                        stage_name = stage_config.get('stage_name', '')
                        
                        print(f"Debug - Inferring approval_type from workflow_name: '{workflow_name}', stage_name: '{stage_name}'")
                        
                        # Look for questionnaire-related keywords in workflow name or stage name
                        if any(keyword in workflow_name.lower() for keyword in ['questionnaire', 'ques']):
                            approval_type = 'questionnaire_approval'
                            print(f"Debug - Detected questionnaire approval from workflow name")
                        elif any(keyword in stage_name.lower() for keyword in ['questionnaire', 'ques']):
                            approval_type = 'questionnaire_approval'
                            print(f"Debug - Detected questionnaire approval from stage name")
                        # If this is a vendor approval workflow and we can't determine the type, 
                        # we need to check if there's a questionnaire_id in the request data
                        elif isinstance(request_data, dict):
                            # Check for questionnaire_id which would indicate questionnaire approval
                            questionnaire_id = request_data.get('questionnaire_id')
                            if not questionnaire_id and 'request_data' in request_data:
                                nested_request_data = request_data.get('request_data', {})
                                if isinstance(nested_request_data, dict):
                                    questionnaire_id = nested_request_data.get('questionnaire_id')
                            
                            if questionnaire_id:
                                approval_type = 'questionnaire_approval'
                                print(f"Debug - Detected questionnaire approval from questionnaire_id: {questionnaire_id}")
                            else:
                                print(f"Debug - No questionnaire_id found, cannot determine approval type")
                    
                    # Normalize approval_type for comparison
                    approval_type_normalized = approval_type.lower().replace(' ', '_') if approval_type else ''
                    is_questionnaire_approval = approval_type_normalized == 'questionnaire_approval'
                    
                    print(f"Debug - approval_type: '{approval_type}' -> normalized: '{approval_type_normalized}' -> is_questionnaire_approval: {is_questionnaire_approval}")
                    print(f"Debug - Full request_data keys: {list(request_data.keys()) if isinstance(request_data, dict) else 'Not a dict'}")
                    if isinstance(request_data, dict) and 'request_data' in request_data:
                        nested_keys = list(request_data['request_data'].keys()) if isinstance(request_data['request_data'], dict) else 'Not a dict'
                        print(f"Debug - Nested request_data keys: {nested_keys}")
                    
                    # Debug: Print the full request_data structure for troubleshooting
                    print(f"Debug - Full request_data: {request_data}")
                    print(f"Debug - workflow_data: {workflow_data}")
                    
                    if (is_questionnaire_approval and initial_stage_status == 'IN_PROGRESS'):
                        print(f"Debug - Questionnaire Approval stage detected, processing lifecycle tracking...")
                        # Start the Questionnaire Approval lifecycle stage
                        try:
                            # Get vendor_id from multiple sources
                            vendor_id = None
                            
                            print(f"Debug - Full request_data structure: {request_data}")
                            print(f"Debug - Full request.data structure: {request.data if hasattr(request, 'data') else 'N/A'}")
                            
                            # PRIORITY 1: Check business_object_id in request_data (primary source from Vue component)
                            if isinstance(request_data, dict):
                                business_object_id = request_data.get('business_object_id')
                                if business_object_id and isinstance(business_object_id, (int, str)) and str(business_object_id).strip():
                                    vendor_id = business_object_id
                                    print(f"Debug - ✓ Found vendor_id in request_data.business_object_id: {vendor_id}")
                            
                            # PRIORITY 2: Check vendor_id directly in request_data
                            if not vendor_id and isinstance(request_data, dict):
                                direct_vendor_id = request_data.get('vendor_id')
                                if direct_vendor_id and str(direct_vendor_id).strip():
                                    vendor_id = direct_vendor_id
                                    print(f"Debug - ✓ Found vendor_id in request_data.vendor_id: {vendor_id}")
                            
                            # PRIORITY 3: Check in nested request_data.request_data structure
                            if not vendor_id and isinstance(request_data, dict):
                                nested_request_data = request_data.get('request_data', {})
                                if nested_request_data and isinstance(nested_request_data, dict):
                                    nested_vendor_id = nested_request_data.get('vendor_id')
                                    if nested_vendor_id and str(nested_vendor_id).strip():
                                        vendor_id = nested_vendor_id
                                        print(f"Debug - ✓ Found vendor_id in nested request_data: {vendor_id}")
                                    
                                    # Also check business_object_id in nested structure
                                    if not vendor_id:
                                        nested_business_object_id = nested_request_data.get('business_object_id')
                                        if nested_business_object_id and str(nested_business_object_id).strip():
                                            vendor_id = nested_business_object_id
                                            print(f"Debug - ✓ Found vendor_id in nested business_object_id: {vendor_id}")
                            
                            # PRIORITY 4: Check business_object_id in the main request body (from Vue requestForm)
                            if not vendor_id and hasattr(request, 'data'):
                                main_business_object_id = request.data.get('request', {}).get('business_object_id')
                                if main_business_object_id and str(main_business_object_id).strip():
                                    vendor_id = main_business_object_id
                                    print(f"Debug - ✓ Found vendor_id in request.data.request.business_object_id: {vendor_id}")
                            
                            # PRIORITY 4.5: Check the main request body structure (Vue sends request.business_object_id)
                            if not vendor_id and hasattr(request, 'data'):
                                request_body = request.data
                                if isinstance(request_body, dict):
                                    # Check if request_data is actually the main request body
                                    main_vendor_id = request_body.get('vendor_id')
                                    if main_vendor_id and str(main_vendor_id).strip():
                                        vendor_id = main_vendor_id
                                        print(f"Debug - ✓ Found vendor_id in main request body: {vendor_id}")
                                    
                                    # Check business_object_id in main request body
                                    if not vendor_id:
                                        main_business_object_id = request_body.get('business_object_id')
                                        if main_business_object_id and str(main_business_object_id).strip():
                                            vendor_id = main_business_object_id
                                            print(f"Debug - ✓ Found vendor_id in main request body business_object_id: {vendor_id}")
                            
                            # PRIORITY 5: Check URL parameters
                            if not vendor_id:
                                request_vendor_id = request.GET.get('vendor_id') or request.POST.get('vendor_id')
                                if request_vendor_id and str(request_vendor_id).strip():
                                    vendor_id = request_vendor_id
                                    print(f"Debug - ✓ Found vendor_id in request URL parameters: {vendor_id}")
                            
                            # If no vendor_id in request data, try to get from questionnaire_id
                            if not vendor_id:
                                questionnaire_id = None
                                
                                # Try to get questionnaire_id from request_data
                                if isinstance(request_data, dict):
                                    questionnaire_id = request_data.get('questionnaire_id')
                                
                                # Try to get questionnaire_id from nested request_data
                                if not questionnaire_id and isinstance(request_data, dict) and isinstance(request_data.get('request_data'), dict):
                                    questionnaire_id = request_data.get('request_data', {}).get('questionnaire_id')
                                
                                if questionnaire_id:
                                    print(f"Debug - No vendor_id in request data, trying to get from questionnaire_id: {questionnaire_id}")
                                    try:
                                        # Fetch vendor_id directly from Questionnaires table
                                        from tprm_backend.apps.vendor_questionnaire.models import Questionnaires
                                        questionnaire = Questionnaires.objects.filter(questionnaire_id=questionnaire_id).first()
                                        if questionnaire and questionnaire.vendor_id:
                                            vendor_id = questionnaire.vendor_id
                                            print(f"✓ Successfully extracted vendor_id {vendor_id} from questionnaire_id {questionnaire_id}")
                                        else:
                                            print(f"WARNING - Questionnaire {questionnaire_id} found but has no vendor_id")
                                            print(f"DEBUG - Questionnaire data: id={questionnaire.questionnaire_id if questionnaire else 'None'}, name={questionnaire.questionnaire_name if questionnaire else 'None'}, vendor_id={questionnaire.vendor_id if questionnaire else 'None'}")
                                    except Exception as e:
                                        print(f"ERROR - Failed to extract vendor_id from questionnaire: {str(e)}")
                                        import traceback
                                        traceback.print_exc()
                                        
                            # If still no vendor_id, try to get from questionnaire_assignment_id
                            if not vendor_id:
                                questionnaire_assignment_id = None
                                
                                # Try to get questionnaire_assignment_id from request_data
                                if isinstance(request_data, dict):
                                    questionnaire_assignment_id = request_data.get('questionnaire_assignment_id')
                                
                                # Try to get questionnaire_assignment_id from nested request_data
                                if not questionnaire_assignment_id and isinstance(request_data, dict) and isinstance(request_data.get('request_data'), dict):
                                    questionnaire_assignment_id = request_data.get('request_data', {}).get('questionnaire_assignment_id')
                                
                                if questionnaire_assignment_id:
                                    print(f"Debug - No vendor_id in request data, trying to get from questionnaire_assignment_id: {questionnaire_assignment_id}")
                                    try:
                                        from tprm_backend.apps.vendor_questionnaire.models import QuestionnaireAssignments
                                        assignment = QuestionnaireAssignments.objects.get(assignment_id=questionnaire_assignment_id)
                                        if assignment.temp_vendor:
                                            vendor_id = assignment.temp_vendor.id
                                            print(f"Debug - Extracted vendor_id {vendor_id} from questionnaire_assignment_id {questionnaire_assignment_id}")
                                    except Exception as e:
                                        print(f"ERROR - Failed to extract vendor_id from assignment: {str(e)}")
                                        import traceback
                                        traceback.print_exc()
                            
                            # Last resort: try to extract vendor ID from the workflow name or other sources
                            if not vendor_id:
                                try:
                                    # Try to get from workflow name first
                                    workflow_id = workflow_data.get('workflow_id')
                                    if workflow_id:
                                        from apps.vendor_approval.models import ApprovalWorkflows
                                        workflow = ApprovalWorkflows.objects.filter(workflow_id=workflow_id).first()
                                        if workflow and workflow.workflow_name:
                                            # Try to extract vendor code from workflow name (e.g. "VEN0046")
                                            import re
                                            vendor_code_match = re.search(r'VEN\d+', workflow.workflow_name)
                                            if vendor_code_match:
                                                vendor_code = vendor_code_match.group(0)
                                                from apps.vendor_core.models import TempVendor
                                                temp_vendor = TempVendor.objects.filter(vendor_code=vendor_code).first()
                                                if temp_vendor:
                                                    vendor_id = temp_vendor.id
                                                    print(f"Debug - Extracted vendor_id {vendor_id} from vendor code {vendor_code} in workflow name")
                                    
                                    # If still no vendor_id, try to get from the stage name (e.g. "Analytics.ai pvt (VEND003)")
                                    if not vendor_id:
                                        stage_name = stage_config.get('stage_name', '')
                                        if stage_name:
                                            # Try to extract vendor code from stage name
                                            import re
                                            vendor_code_match = re.search(r'VEND\d+', stage_name)
                                            if vendor_code_match:
                                                vendor_code = vendor_code_match.group(0)
                                                from apps.vendor_core.models import TempVendor
                                                temp_vendor = TempVendor.objects.filter(vendor_code=vendor_code).first()
                                                if temp_vendor:
                                                    vendor_id = temp_vendor.id
                                                    print(f"Debug - Extracted vendor_id {vendor_id} from vendor code {vendor_code} in stage name")
                                    
                                    # If still no vendor_id, try to get from the request title
                                    if not vendor_id and isinstance(request_data, dict):
                                        request_title = request_data.get('request_title', '')
                                        if request_title:
                                            # Try to extract vendor code from request title
                                            import re
                                            vendor_code_match = re.search(r'VEND\d+', request_title)
                                            if vendor_code_match:
                                                vendor_code = vendor_code_match.group(0)
                                                from apps.vendor_core.models import TempVendor
                                                temp_vendor = TempVendor.objects.filter(vendor_code=vendor_code).first()
                                                if temp_vendor:
                                                    vendor_id = temp_vendor.id
                                                    print(f"Debug - Extracted vendor_id {vendor_id} from vendor code {vendor_code} in request title")
                                    
                                except Exception as e:
                                    print(f"ERROR - Failed to extract vendor_id from workflow name: {str(e)}")
                                    import traceback
                                    traceback.print_exc()
                            
                            if vendor_id:
                                # Ensure vendor_id is an integer
                                vendor_id = int(vendor_id) if str(vendor_id).isdigit() else None
                                
                                if vendor_id:
                                    # Get the Questionnaire Approval stage ID (stage_code = 'QUES_APP')
                                    cursor.execute("""
                                        SELECT stage_id, stage_name, stage_code FROM vendor_lifecycle_stages 
                                        WHERE stage_code = 'QUES_APP' AND is_active = 1
                                    """)
                                    ques_app_stage = cursor.fetchone()
                                    print(f"Debug - QUES_APP stage lookup result: {ques_app_stage}")
                                    
                                    # Also check all available stages for debugging
                                    cursor.execute("""
                                        SELECT stage_id, stage_name, stage_code FROM vendor_lifecycle_stages 
                                        WHERE is_active = 1 ORDER BY stage_order
                                    """)
                                    all_stages = cursor.fetchall()
                                    print(f"Debug - All available lifecycle stages: {all_stages}")
                                    
                                    if ques_app_stage:
                                        ques_app_stage_id = ques_app_stage[0]
                                        print(f"Debug - Found QUES_APP stage_id: {ques_app_stage_id}")
                                        
                                        # Use the helper function to ensure lifecycle stage exists
                                        # First commit the current transaction to avoid conflicts
                                        connections[db_connection].commit()
                                        
                                        # Ensure lifecycle stage exists (for tracking only, not for approval_stages)
                                        from django.db import transaction
                                        with transaction.atomic():
                                            lifecycle_stage_id = ensure_lifecycle_stage_exists(vendor_id, 'QUES_APP')
                                            if lifecycle_stage_id:
                                                print(f"✓ Successfully ensured Lifecycle Stage 3 (Questionnaire Approval) for vendor {vendor_id} with lifecycle_stage_id {lifecycle_stage_id}")
                                            else:
                                                print(f"ERROR - Failed to ensure Lifecycle Stage 3 for vendor {vendor_id}")
                                                
                                        # Continue with the current transaction
                                    else:
                                        print(f"ERROR - No QUES_APP stage found in vendor_lifecycle_stages table")
                                else:
                                    print(f"WARNING - vendor_id could not be converted to integer")
                            else:
                                print(f"WARNING - No vendor_id found in request data for Questionnaire Approval stage")
                                print(f"DEBUG - Full request_data: {request_data}")
                        except Exception as e:
                            print(f"ERROR - Failed to start Questionnaire Approval lifecycle stage: {str(e)}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"Debug - Stage '{stage_config.get('stage_name', '')}' does not match Questionnaire Approval or status is not IN_PROGRESS")

                    

                    # Initialize response_data for each stage

                    initial_response_data = standardize_response_data(

                        response_data={},

                        stage_status=initial_stage_status,

                        decision='',

                        comments='',

                        rejection_reason=''

                    )

                    

                    print(f"Debug - Initializing response_data for stage {stage_id} (order {stage_config.get('stage_order', 1)}) with status {initial_stage_status}")

                    

                    # Note: weightage column doesn't exist in approval_stages table
                    # escalation_level is required but doesn't have a default value
                    cursor.execute("""

                        INSERT INTO approval_stages 

                        (stage_id, approval_id, stage_order, stage_name, stage_description, 

                         assigned_user_id, assigned_user_name, assigned_user_role, department, 

                         stage_type, stage_status, deadline_date, started_at, response_data, escalation_level, is_mandatory, TenantId, created_at, updated_at) 

                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

                    """, [

                        stage_id,

                        approval_id,

                        stage_config.get('stage_order', 1),

                        stage_config.get('stage_name', ''),

                        stage_config.get('stage_description', ''),

                        stage_config.get('assigned_user_id'),  # Use selected user from dropdown

                        stage_config.get('assigned_user_name', ''),  # Use selected user name from dropdown

                        stage_config.get('assigned_user_role', ''),  # Use selected user role from dropdown

                        stage_config.get('department', ''),

                        stage_config.get('stage_type', 'SEQUENTIAL'),

                        initial_stage_status,

                        deadline_date or timezone.now(),

                        started_at,

                        json.dumps(initial_response_data),

                        stage_config.get('escalation_level', 0),  # Default escalation level is 0

                        stage_config.get('is_mandatory', True),

                        tenant_id,

                        timezone.now(),

                        timezone.now()

                    ])

                

                # 4. Create initial version only for MULTI_LEVEL workflows (version control needed)

                if workflow_data.get('workflow_type') == 'MULTI_LEVEL':

                    version_id = str(uuid.uuid4()).replace('-', '').upper()[:16]

                    cursor.execute("""

                        INSERT INTO approval_request_versions 

                        (version_id, approval_id, version_number, version_label, json_payload, 

                         changes_summary, created_by, created_by_name, created_by_role, 

                         version_type, is_current, created_at) 

                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

                    """, [

                        version_id,

                        approval_id,

                        1,  # Initial version

                        'Initial Submission',

                        json.dumps(request_data),

                        'Initial request submission',

                        60,

                        'GRC Administrator',

                        'Requester',

                        'INITIAL',

                        True,  # Current version

                        timezone.now()

                    ])

                

                # Re-enable foreign key checks

                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

                # Commit using the same connection that was used for the cursor
                connections[db_connection].commit()

                

                print(f"Created comprehensive workflow with request: {workflow_id} -> {approval_id}")

                print(f"Debug - Created {len(stages_data)} stages with initialized response_data for workflow type: {workflow_data.get('workflow_type')}")

                

                # Determine the correct status for the response

                response_status = 'IN_PROGRESS' if workflow_data.get('workflow_type') == 'MULTI_PERSON' else 'PENDING'

                
                # Handle lifecycle stage transitions for questionnaire approval
                try:
                    # Extract vendor_id from multiple possible sources
                    vendor_id = None
                    
                    # First, check direct vendor_id in request body
                    if 'vendor_id' in data:
                        vendor_id = data.get('vendor_id')
                    
                    # Second, check business_object_id in request body
                    if not vendor_id and 'business_object_id' in data:
                        vendor_id = data.get('business_object_id')
                    
                    # Third, check request_data nested structure
                    if not vendor_id and request_data:
                        rd = request_data.get('request_data', request_data)
                        if isinstance(rd, dict):
                            vendor_id = rd.get('vendor_id') or rd.get('business_object_id')
                    
                    # Fourth, check if vendor_id is in workflow_data
                    if not vendor_id and workflow_data:
                        vendor_id = workflow_data.get('vendor_id') or workflow_data.get('business_object_id')
                    
                    # Fifth, try to extract from questionnaire if it's questionnaire approval
                    if not vendor_id and request_data:
                        rd = request_data.get('request_data', request_data)
                        if isinstance(rd, dict):
                            approval_type = rd.get('approval_type', '').lower().replace(' ', '_')
                            if approval_type == 'questionnaire_approval':
                                questionnaire_id = rd.get('questionnaire_id')
                                if questionnaire_id:
                                    try:
                                        from tprm_backend.apps.vendor_questionnaire.models import Questionnaires
                                        questionnaire = Questionnaires.objects.filter(questionnaire_id=questionnaire_id).first()
                                        if questionnaire and questionnaire.vendor_id:
                                            vendor_id = questionnaire.vendor_id
                                            print(f"✓ Successfully extracted vendor_id {vendor_id} from questionnaire_id {questionnaire_id}")
                                        else:
                                            print(f"WARNING - Questionnaire {questionnaire_id} found but has no vendor_id assigned")
                                    except Exception as e:
                                        print(f"Warning: Could not fetch questionnaire {questionnaire_id}: {str(e)}")
                    
                    # Convert vendor_id to integer if possible
                    if vendor_id:
                        vendor_id = int(vendor_id) if str(vendor_id).isdigit() else None
                    
                    print(f"Debug - create_comprehensive_workflow: vendor_id = {vendor_id}")
                    
                    # Start Lifecycle Stage 3 (Questionnaire Approval) if this is a questionnaire approval workflow
                    if vendor_id and request_data:
                        rd = request_data.get('request_data', request_data)
                        if isinstance(rd, dict):
                            approval_type = rd.get('approval_type', '').lower().replace(' ', '_')
                            
                            if approval_type == 'questionnaire_approval' and workflow_data.get('workflow_type') == 'MULTI_PERSON':
                                print(f"✓ Detected MULTI_PERSON questionnaire_approval workflow for vendor {vendor_id}")
                                print(f"✓ Starting Lifecycle Stage 3 (Questionnaire Approval) for vendor {vendor_id}")
                                
                                # Ensure the vendor is at Questionnaire Approval stage
                                try:
                                    from apps.vendor_core.models import LifecycleTracker, TempVendor
                                    from apps.vendor_core.views import get_lifecycle_stage_id_by_code
                                    
                                    # Get Questionnaire Approval stage ID (Stage 3)
                                    ques_approval_stage_id = get_lifecycle_stage_id_by_code('QUES_APP')
                                    
                                    if ques_approval_stage_id:
                                        # Check if stage already exists
                                        existing_entry = LifecycleTracker.objects.filter(
                                            vendor_id=vendor_id,
                                            lifecycle_stage=ques_approval_stage_id,
                                            ended_at__isnull=True
                                        ).first()
                                        
                                        if not existing_entry:
                                            # Create Questionnaire Approval stage entry
                                            LifecycleTracker.objects.create(
                                                vendor_id=vendor_id,
                                                lifecycle_stage=ques_approval_stage_id,
                                                started_at=timezone.now()
                                            )
                                            
                                            # Update temp vendor lifecycle stage
                                            try:
                                                temp_vendor = TempVendor.objects.get(id=vendor_id)
                                                temp_vendor.lifecycle_stage = ques_approval_stage_id
                                                temp_vendor.save()
                                                print(f"✓ Successfully started Lifecycle Stage 3 (Questionnaire Approval) for vendor {vendor_id}")
                                            except TempVendor.DoesNotExist:
                                                print(f"Warning: TempVendor with ID {vendor_id} not found")
                                        else:
                                            print(f"✓ Lifecycle Stage 3 (Questionnaire Approval) already active for vendor {vendor_id}")
                                    else:
                                        print(f"Warning: Could not find QUES_APP stage ID")
                                        
                                except Exception as e:
                                    print(f"Warning: Failed to start Lifecycle Stage 3 for vendor {vendor_id}: {str(e)}")
                                    import traceback
                                    traceback.print_exc()
                            
                except Exception as e:
                    print(f"Warning: Error handling lifecycle stages: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # Don't fail the workflow creation if lifecycle stage update fails

                

                return Response({

                    'workflow_id': workflow_id,

                    'approval_id': approval_id,

                    'message': 'Workflow, request, and stages created successfully',

                    'status': response_status,

                    'vendor_id': vendor_id if vendor_id else None

                }, status=status.HTTP_201_CREATED)

                

        except Exception as e:

            print(f"Database error: {str(e)}")

            return Response({

                'error': 'Failed to create comprehensive workflow in database',

                'details': str(e)

            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            

    except Exception as e:

        print(f"General error: {str(e)}")

        return Response({

            'error': 'Failed to process comprehensive workflow creation request',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_active_questionnaires(request):

    """Get all active questionnaires for selection
    MULTI-TENANCY: Questionnaires may be shared across tenants
    NOTE: Questionnaires table is in tprm_integration database, not default database
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        # Use 'tprm' connection to access questionnaires table in tprm_integration database
        # Fall back to 'default' if 'tprm' connection is not available
        db_connection = 'tprm'
        try:
            # Check if 'tprm' connection exists
            if 'tprm' not in connections.databases:
                print("Warning: 'tprm' database connection not found, falling back to 'default'")
                db_connection = 'default'
            else:
                print(f"Using 'tprm' database connection for questionnaires table (tprm_integration)")
        except Exception as db_check_error:
            print(f"Warning: Error checking database connections: {db_check_error}, using 'tprm' connection")

        with connections[db_connection].cursor() as cursor:

            # First check if questionnaires table exists and has data

            cursor.execute("""

                SELECT COUNT(*) as total_count

                FROM questionnaires

            """)

            total_count = cursor.fetchone()[0]

            print(f"Total questionnaires in database: {total_count}")

            

            # Get active questionnaires

            cursor.execute("""

                SELECT questionnaire_id, questionnaire_name, questionnaire_type, 

                       description, version, created_at

                FROM questionnaires 

                WHERE status = 'ACTIVE'

                ORDER BY questionnaire_name

            """)

            columns = [col[0] for col in cursor.description]

            questionnaires = [dict(zip(columns, row)) for row in cursor.fetchall()]

            

            print(f"Active questionnaires found: {len(questionnaires)}")

            

            # If no active questionnaires, try to get any questionnaires

            if not questionnaires:

                cursor.execute("""

                    SELECT questionnaire_id, questionnaire_name, questionnaire_type, 

                           description, version, created_at, status

                    FROM questionnaires 

                    ORDER BY questionnaire_name

                """)

                columns = [col[0] for col in cursor.description]

                all_questionnaires = [dict(zip(columns, row)) for row in cursor.fetchall()]

                print(f"All questionnaires found: {len(all_questionnaires)}")

                

                # Return all questionnaires if no active ones

                questionnaires = all_questionnaires

            

            return Response(questionnaires, status=status.HTTP_200_OK)

            

    except Exception as e:

        print(f"Error fetching active questionnaires: {str(e)}")

        return Response({

            'error': 'Failed to fetch active questionnaires',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('create_vendor')
@require_tenant
@tenant_filter
def add_dummy_users(request):

    """Add dummy users to the users table for testing
    MULTI-TENANCY: Admin function for testing
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        with connections['default'].cursor() as cursor:

            # Check if users already exist

            cursor.execute("SELECT COUNT(*) FROM users")

            existing_count = cursor.fetchone()[0]

            

            if existing_count > 0:

                return Response({

                    'message': f'Users table already has {existing_count} users',

                    'warning': 'Users already exist'

                }, status=status.HTTP_200_OK)

            

            dummy_users = [

                ('John Admin', 'john.admin@company.com', 'admin123'),

                ('Jane Manager', 'jane.manager@company.com', 'manager123'),

                ('Bob Employee', 'bob.employee@company.com', 'employee123'),

                ('Alice Finance', 'alice.finance@company.com', 'finance123'),

                ('Charlie IT', 'charlie.it@company.com', 'it123'),

                ('Diana HR', 'diana.hr@company.com', 'hr123'),

                ('Eve Operations', 'eve.operations@company.com', 'ops123'),

                ('Frank Security', 'frank.security@company.com', 'security123'),

                ('Grace Legal', 'grace.legal@company.com', 'legal123'),

                ('Henry Compliance', 'henry.compliance@company.com', 'compliance123')

            ]

            

            for user_name, email, password in dummy_users:

                cursor.execute("""

                    INSERT INTO users (UserName, Email, Password, CreatedAt, UpdatedAt) 

                    VALUES (%s, %s, %s, %s, %s)

                """, [user_name, email, password, timezone.now(), timezone.now()])

            

            connection.commit()

            

            return Response({

                'message': f'Successfully added {len(dummy_users)} dummy users to the database',

                'count': len(dummy_users)

            }, status=status.HTTP_201_CREATED)

            

    except Exception as e:

        print(f"Error adding dummy users: {str(e)}")

        return Response({

            'error': 'Failed to add dummy users',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_vendors(request):

    """
    Get all vendors from temp_vendor table for selection in final vendor approval
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation

    Returns:

        List of vendors with essential information for dropdown selection

    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        # Use tprm database connection for vendor queries
        db_connection = 'tprm'
        try:
            if 'tprm' not in connections.databases:
                print("Warning: 'tprm' database connection not found, falling back to 'default'")
                db_connection = 'default'
        except Exception as db_check_error:
            print(f"Warning: Error checking database connections: {db_check_error}, using 'tprm' connection")

        with connections[db_connection].cursor() as cursor:
            # MULTI-TENANCY: Get vendors from temp_vendor table filtered by TenantId
            cursor.execute("""
                SELECT 
                    id, vendor_code, company_name, legal_name, business_type,
                    industry_sector, risk_level, status, vendor_category,
                    is_critical_vendor, has_data_access, has_system_access,
                    website, annual_revenue, employee_count, headquarters_address,
                    description, created_at, updated_at
                FROM temp_vendor
                WHERE TenantId = %s
                ORDER BY company_name
            """, [tenant_id])

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            vendor_list = []
            for row in rows:
                vendor_dict = dict(zip(columns, row))
                vendor_data = {
                    'id': vendor_dict.get('id'),
                    'vendor_code': vendor_dict.get('vendor_code', ''),
                    'company_name': vendor_dict.get('company_name', ''),
                    'legal_name': vendor_dict.get('legal_name', ''),
                    'business_type': vendor_dict.get('business_type', ''),
                    'industry_sector': vendor_dict.get('industry_sector', ''),
                    'risk_level': vendor_dict.get('risk_level', ''),
                    'status': vendor_dict.get('status', ''),
                    'vendor_category': vendor_dict.get('vendor_category', ''),
                    'is_critical_vendor': vendor_dict.get('is_critical_vendor', False),
                    'has_data_access': vendor_dict.get('has_data_access', False),
                    'has_system_access': vendor_dict.get('has_system_access', False),
                    'website': vendor_dict.get('website', ''),
                    'annual_revenue': str(vendor_dict.get('annual_revenue', '')) if vendor_dict.get('annual_revenue') else None,
                    'employee_count': vendor_dict.get('employee_count'),
                    'headquarters_address': vendor_dict.get('headquarters_address', ''),
                    'description': vendor_dict.get('description', ''),
                    'created_at': vendor_dict.get('created_at').isoformat() if vendor_dict.get('created_at') else None,
                    'updated_at': vendor_dict.get('updated_at').isoformat() if vendor_dict.get('updated_at') else None
                }
                vendor_list.append(vendor_data)

        return Response({
            'vendors': vendor_list,
            'count': len(vendor_list)
        }, status=status.HTTP_200_OK)

        

    except Exception as e:

        print(f"Error fetching vendors: {str(e)}")

        return Response({

            'error': 'Failed to fetch vendors',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_vendor_detail(request, vendor_id):

    """
    Get detailed information for a specific vendor by ID
    MULTI-TENANCY: Ensures vendor belongs to tenant

    Args:

        vendor_id: ID of the vendor to fetch

        

    Returns:

        Detailed vendor information

    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        # Use tprm database connection for vendor queries
        db_connection = 'tprm'
        try:
            if 'tprm' not in connections.databases:
                print("Warning: 'tprm' database connection not found, falling back to 'default'")
                db_connection = 'default'
        except Exception as db_check_error:
            print(f"Warning: Error checking database connections: {db_check_error}, using 'tprm' connection")

        with connections[db_connection].cursor() as cursor:
            # MULTI-TENANCY: Get vendor by ID and TenantId
            cursor.execute("""
                SELECT 
                    id, vendor_code, company_name, legal_name, business_type,
                    tax_id, duns_number, incorporation_date, industry_sector,
                    website, annual_revenue, employee_count, headquarters_address,
                    vendor_category, risk_level, status, is_critical_vendor,
                    has_data_access, has_system_access, description,
                    contacts, documents, created_at, updated_at
                FROM temp_vendor
                WHERE id = %s AND TenantId = %s
            """, [vendor_id, tenant_id])

            row = cursor.fetchone()
            
            if not row:
                return Response({
                    'error': 'Vendor not found',
                    'details': f'No vendor found with ID {vendor_id} for tenant {tenant_id}'
                }, status=status.HTTP_404_NOT_FOUND)

            columns = [col[0] for col in cursor.description]
            vendor_dict = dict(zip(columns, row))

            vendor_data = {
                'id': vendor_dict.get('id'),
                'vendor_code': vendor_dict.get('vendor_code', ''),
                'company_name': vendor_dict.get('company_name', ''),
                'legal_name': vendor_dict.get('legal_name', ''),
                'business_type': vendor_dict.get('business_type', ''),
                'tax_id': vendor_dict.get('tax_id', ''),
                'duns_number': vendor_dict.get('duns_number', ''),
                'incorporation_date': vendor_dict.get('incorporation_date').isoformat() if vendor_dict.get('incorporation_date') else None,
                'industry_sector': vendor_dict.get('industry_sector', ''),
                'website': vendor_dict.get('website', ''),
                'annual_revenue': str(vendor_dict.get('annual_revenue', '')) if vendor_dict.get('annual_revenue') else None,
                'employee_count': vendor_dict.get('employee_count'),
                'headquarters_address': vendor_dict.get('headquarters_address', ''),
                'vendor_category': vendor_dict.get('vendor_category', ''),
                'risk_level': vendor_dict.get('risk_level', ''),
                'status': vendor_dict.get('status', ''),
                'is_critical_vendor': vendor_dict.get('is_critical_vendor', False),
                'has_data_access': vendor_dict.get('has_data_access', False),
                'has_system_access': vendor_dict.get('has_system_access', False),
                'description': vendor_dict.get('description', ''),
                'contacts': vendor_dict.get('contacts'),
                'documents': vendor_dict.get('documents'),
                'created_at': vendor_dict.get('created_at').isoformat() if vendor_dict.get('created_at') else None,
                'updated_at': vendor_dict.get('updated_at').isoformat() if vendor_dict.get('updated_at') else None
            }

        return Response(vendor_data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error fetching vendor detail: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Check if it's a "not found" type error
        if 'not found' in str(e).lower() or 'does not exist' in str(e).lower():
            return Response({
                'error': 'Vendor not found',
                'details': f'No vendor found with ID {vendor_id}'
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'error': 'Failed to fetch vendor details',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# Dashboard API Endpoints

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def dashboard_stats(request):

    """Get dashboard statistics for approval system
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        # Use tprm database connection for vendor approval queries
        cursor = connections['tprm'].cursor()

        # Get basic counts filtered by business_object_type = 'Vendor' and tenant
        # MULTI-TENANCY: Filter by tenant
        # Use temp_vendor from tprm database (no database prefix needed since we're using tprm connection)
        cursor.execute("""

            SELECT 

                COUNT(*) as total_requests,

                SUM(CASE WHEN a.overall_status = 'PENDING' THEN 1 ELSE 0 END) as pending_requests,

                SUM(CASE WHEN a.overall_status = 'IN_PROGRESS' THEN 1 ELSE 0 END) as in_progress_requests,

                SUM(CASE WHEN a.overall_status = 'APPROVED' THEN 1 ELSE 0 END) as approved_requests,

                SUM(CASE WHEN a.overall_status = 'REJECTED' THEN 1 ELSE 0 END) as rejected_requests

            FROM approval_requests a

            JOIN approval_workflows w ON a.workflow_id = w.workflow_id
            
            LEFT JOIN temp_vendor tv ON JSON_EXTRACT(a.request_data, '$.vendor_id') = tv.id

            WHERE w.business_object_type = 'Vendor'

            AND (tv.TenantId = %s OR tv.TenantId IS NULL)

        """, [tenant_id])

        result = cursor.fetchone()

        total_requests = result[0] or 0

        pending_requests = result[1] or 0

        in_progress_requests = result[2] or 0

        approved_requests = result[3] or 0

        rejected_requests = result[4] or 0

        

        # Get workflow type breakdown filtered by business_object_type = 'Vendor' and tenant
        # MULTI-TENANCY: Filter by tenant
        # Use temp_vendor since the table exists in that database
        cursor.execute("""

            SELECT 

                w.workflow_type,

                COUNT(*) as count

            FROM approval_requests a

            JOIN approval_workflows w ON a.workflow_id = w.workflow_id
            
            LEFT JOIN temp_vendor tv ON JSON_EXTRACT(a.request_data, '$.vendor_id') = tv.id

            WHERE w.business_object_type = 'Vendor'
            
            AND (tv.TenantId = %s OR tv.TenantId IS NULL)

            GROUP BY w.workflow_type

        """, [tenant_id])

        workflow_breakdown = {}

        for row in cursor.fetchall():

            workflow_breakdown[row[0]] = row[1]

        

        # Get priority breakdown filtered by business_object_type = 'Vendor' and tenant
        # MULTI-TENANCY: Filter by tenant
        # Use temp_vendor since the table exists in that database
        cursor.execute("""

            SELECT 

                a.priority,

                COUNT(*) as count

            FROM approval_requests a

            JOIN approval_workflows w ON a.workflow_id = w.workflow_id
            
            LEFT JOIN temp_vendor tv ON JSON_EXTRACT(a.request_data, '$.vendor_id') = tv.id

            WHERE w.business_object_type = 'Vendor'
            
            AND (tv.TenantId = %s OR tv.TenantId IS NULL)

            GROUP BY a.priority

        """, [tenant_id])

        priority_breakdown = {}

        for row in cursor.fetchall():

            priority_breakdown[row[0]] = row[1]

        

        # Get recent activity (last 7 days) filtered by business_object_type = 'Vendor'

        from django.utils import timezone

        from datetime import timedelta

        

        week_ago = timezone.now() - timedelta(days=7)
        
        # Use temp_vendor since the table exists in that database
        cursor.execute("""

            SELECT COUNT(*) as recent_activity

            FROM approval_requests a

            JOIN approval_workflows w ON a.workflow_id = w.workflow_id
            
            LEFT JOIN temp_vendor tv ON JSON_EXTRACT(a.request_data, '$.vendor_id') = tv.id

            WHERE w.business_object_type = 'Vendor'
            
            AND (tv.TenantId = %s OR tv.TenantId IS NULL)

            AND a.created_at >= %s

        """, [tenant_id, week_ago])

        result = cursor.fetchone()

        recent_activity = result[0] or 0

        

        return Response({

            'total_requests': total_requests,

            'pending_requests': pending_requests,

            'in_progress_requests': in_progress_requests,

            'approved_requests': approved_requests,

            'rejected_requests': rejected_requests,

            'workflow_breakdown': workflow_breakdown,

            'priority_breakdown': priority_breakdown,

            'recent_activity': recent_activity

        })

        

    except Exception as e:

        print(f"Error in dashboard stats: {str(e)}")
        import traceback
        traceback.print_exc()

        # Fallback to basic counts filtered by business_object_type = 'Vendor'
        try:
            # Use tprm database connection for vendor approval queries
            cursor = connections['tprm'].cursor()
            
            # Use temp_vendor from tprm database (no database prefix needed since we're using tprm connection)
            cursor.execute("""

                SELECT 

                    COUNT(*) as total_requests,

                    SUM(CASE WHEN a.overall_status = 'PENDING' THEN 1 ELSE 0 END) as pending_requests,

                    SUM(CASE WHEN a.overall_status = 'IN_PROGRESS' THEN 1 ELSE 0 END) as in_progress_requests,

                    SUM(CASE WHEN a.overall_status = 'APPROVED' THEN 1 ELSE 0 END) as approved_requests,

                    SUM(CASE WHEN a.overall_status = 'REJECTED' THEN 1 ELSE 0 END) as rejected_requests

                FROM approval_requests a

                JOIN approval_workflows w ON a.workflow_id = w.workflow_id
                
                LEFT JOIN temp_vendor tv ON JSON_EXTRACT(a.request_data, '$.vendor_id') = tv.id

                WHERE w.business_object_type = 'Vendor'
                
                AND (tv.TenantId = %s OR tv.TenantId IS NULL)

            """, [tenant_id])

            result = cursor.fetchone()

            total_requests = result[0] or 0 if result else 0

            pending_requests = result[1] or 0 if result and len(result) > 1 else 0

            in_progress_requests = result[2] or 0 if result and len(result) > 2 else 0

            approved_requests = result[3] or 0 if result and len(result) > 3 else 0

            rejected_requests = result[4] or 0 if result and len(result) > 4 else 0

        except Exception as fallback_error:
            print(f"Error in fallback query: {str(fallback_error)}")
            total_requests = 0
            pending_requests = 0
            in_progress_requests = 0
            approved_requests = 0
            rejected_requests = 0

        return Response({

            'total_requests': total_requests,

            'pending_requests': pending_requests,

            'in_progress_requests': in_progress_requests,

            'approved_requests': approved_requests,

            'rejected_requests': rejected_requests,

            'workflow_breakdown': {},

            'priority_breakdown': {},

            'recent_activity': 0

        })





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def recent_requests(request):

    """Get recent approval requests for dashboard
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        # Use tprm database connection for vendor approval queries
        cursor = connections['tprm'].cursor()

        

        # Check if tables exist first

        cursor.execute("SHOW TABLES LIKE 'approval_requests'")

        if not cursor.fetchone():

            print("approval_requests table does not exist, returning empty data")

            return Response([])

            

        cursor.execute("SHOW TABLES LIKE 'approval_workflows'")

        if not cursor.fetchone():

            print("approval_workflows table does not exist, returning empty data")

            return Response([])

        
        # Fetch recent requests with workflow details
        # MULTI-TENANCY: Filter by tenant
        # Use temp_vendor from tprm database (no database prefix needed since we're using tprm connection)
        cursor.execute("""

            SELECT 

                a.approval_id, a.request_title, a.request_description, a.requester_id,

                a.requester_department, a.priority, a.request_data, a.overall_status, 

                a.submission_date, a.completion_date, a.expiry_date, a.created_at, a.updated_at,

                w.workflow_name, w.workflow_type, w.description as workflow_description

            FROM approval_requests a

            JOIN approval_workflows w ON a.workflow_id = w.workflow_id
            
            LEFT JOIN temp_vendor tv ON JSON_EXTRACT(a.request_data, '$.vendor_id') = tv.id

            WHERE w.business_object_type = 'Vendor'
            
            AND (tv.TenantId = %s OR tv.TenantId IS NULL)

            ORDER BY a.created_at DESC

            LIMIT 10

        """, [tenant_id])

        

        columns = [col[0] for col in cursor.description]

        requests_data = []

        

        for row in cursor.fetchall():

            request_dict = dict(zip(columns, row))

            

            # Parse JSON fields

            if request_dict.get('request_data'):

                try:

                    request_dict['request_data'] = json.loads(request_dict['request_data'])

                except:

                    request_dict['request_data'] = {}

            

            requests_data.append(request_dict)

        

        return Response(requests_data)

        

    except Exception as e:

        print(f"Error fetching recent requests: {str(e)}")

        # Return empty array instead of 500 error to prevent frontend crashes

        return Response([])





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def user_tasks(request, user_id):

    """Get tasks assigned to a specific user for dashboard
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        # Use tprm database connection for vendor approval queries
        cursor = connections['tprm'].cursor()

        

        # Check if tables exist first

        cursor.execute("SHOW TABLES LIKE 'approval_stages'")

        if not cursor.fetchone():

            print("approval_stages table does not exist, returning empty data")

            return Response([])

            

        cursor.execute("SHOW TABLES LIKE 'approval_requests'")

        if not cursor.fetchone():

            print("approval_requests table does not exist, returning empty data")

            return Response([])

            

        cursor.execute("SHOW TABLES LIKE 'approval_workflows'")

        if not cursor.fetchone():

            print("approval_workflows table does not exist, returning empty data")

            return Response([])

        
        # Fetch user's assigned stages that are pending or in progress
        # MULTI-TENANCY: Filter by tenant
        # Use temp_vendor from tprm database (no database prefix needed since we're using tprm connection)
        cursor.execute("""

            SELECT 

                s.stage_id, s.approval_id, s.stage_order, s.stage_name, s.stage_description,

                s.assigned_user_id, s.assigned_user_name, s.assigned_user_role, s.department,

                s.stage_type, s.stage_status, s.deadline_date, s.extended_deadline,

                s.started_at, s.completed_at, s.response_data, s.rejection_reason,

                s.escalation_level, s.is_mandatory, s.created_at, s.updated_at,

                a.request_title, a.request_description, a.requester_id, a.requester_department,

                a.priority, a.request_data, a.overall_status, a.submission_date, 

                a.completion_date, a.expiry_date, a.created_at as request_created_at, 

                a.updated_at as request_updated_at, w.workflow_name, w.workflow_type

            FROM approval_stages s

            JOIN approval_requests a ON s.approval_id = a.approval_id

            JOIN approval_workflows w ON a.workflow_id = w.workflow_id
            
            LEFT JOIN temp_vendor tv ON JSON_EXTRACT(a.request_data, '$.vendor_id') = tv.id

            WHERE s.assigned_user_id = %s 

            AND s.stage_status IN ('PENDING', 'IN_PROGRESS')

            AND w.business_object_type = 'Vendor'
            
            AND (tv.TenantId = %s OR tv.TenantId IS NULL)

            ORDER BY s.deadline_date ASC, s.created_at DESC

            LIMIT 10

        """, [user_id, tenant_id])

        

        columns = [col[0] for col in cursor.description]

        tasks_data = []

        

        for row in cursor.fetchall():

            task_dict = dict(zip(columns, row))

            

            # Parse JSON fields

            if task_dict.get('response_data'):

                try:

                    task_dict['response_data'] = json.loads(task_dict['response_data'])

                except:

                    task_dict['response_data'] = {}

            

            if task_dict.get('request_data'):

                try:

                    task_dict['request_data'] = json.loads(task_dict['request_data'])

                except:

                    task_dict['request_data'] = {}

            

            tasks_data.append(task_dict)

        

        return Response(tasks_data)

        

    except Exception as e:

        print(f"Error fetching user tasks: {str(e)}")

        # Return empty array instead of 500 error to prevent frontend crashes

        return Response([])





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def user_requests(request, user_id):

    """Get requests created by a specific user for dashboard
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        # Use tprm database connection for vendor approval queries
        cursor = connections['tprm'].cursor()

        

        # Check if tables exist first

        cursor.execute("SHOW TABLES LIKE 'approval_requests'")

        if not cursor.fetchone():

            print("approval_requests table does not exist, returning empty data")

            return Response([])

            

        cursor.execute("SHOW TABLES LIKE 'approval_workflows'")

        if not cursor.fetchone():

            print("approval_workflows table does not exist, returning empty data")

            return Response([])

        
        # Fetch requests created by the user with workflow details
        # MULTI-TENANCY: Filter by tenant
        # Use temp_vendor from tprm database (no database prefix needed since we're using tprm connection)
        cursor.execute("""

            SELECT 

                a.approval_id, a.request_title, a.request_description, a.requester_id,

                a.requester_department, a.priority, a.request_data, a.overall_status, 

                a.submission_date, a.completion_date, a.expiry_date, a.created_at, a.updated_at,

                w.workflow_name, w.workflow_type, w.description as workflow_description

            FROM approval_requests a

            JOIN approval_workflows w ON a.workflow_id = w.workflow_id
            
            LEFT JOIN temp_vendor tv ON JSON_EXTRACT(a.request_data, '$.vendor_id') = tv.id

            WHERE a.requester_id = %s

            AND w.business_object_type = 'Vendor'
            
            AND (tv.TenantId = %s OR tv.TenantId IS NULL)

            ORDER BY a.created_at DESC

            LIMIT 10

        """, [user_id, tenant_id])

        

        columns = [col[0] for col in cursor.description]

        requests_data = []

        

        for row in cursor.fetchall():

            request_dict = dict(zip(columns, row))

            

            # Parse JSON fields

            if request_dict.get('request_data'):

                try:

                    request_dict['request_data'] = json.loads(request_dict['request_data'])

                except:

                    request_dict['request_data'] = {}

            

            requests_data.append(request_dict)

        

        return Response(requests_data)

        

    except Exception as e:

        print(f"Error fetching user requests: {str(e)}")

        # Return empty array instead of 500 error to prevent frontend crashes

        return Response([])





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_vendor_risks(request, vendor_id):

    """
    Get all risks associated with a specific vendor - both internal and external
    MULTI-TENANCY: Ensures vendor belongs to tenant

    Args:

        vendor_id: ID of the vendor to fetch risks for

        

    Returns:

        Separate lists of internal risks (from tprm_risk) and external risks (from screening with ESCALATED status)

    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        # MULTI-TENANCY: Verify vendor belongs to tenant using tprm database
        db_connection = 'tprm'
        try:
            if 'tprm' not in connections.databases:
                print("Warning: 'tprm' database connection not found, falling back to 'default'")
                db_connection = 'default'
        except Exception as db_check_error:
            print(f"Warning: Error checking database connections: {db_check_error}, using 'tprm' connection")

        with connections[db_connection].cursor() as cursor:
            cursor.execute("""
                SELECT id FROM temp_vendor
                WHERE id = %s AND TenantId = %s
            """, [vendor_id, tenant_id])
            
            vendor_row = cursor.fetchone()
            if not vendor_row:
                return Response({
                    'error': 'Vendor not found or does not belong to your tenant'
                }, status=status.HTTP_404_NOT_FOUND)

        # Get internal risks from risk_tprm table where entity=vendor_management and row matches vendor_id
        # MULTI-TENANCY: Filter by tenant by joining with temp_vendor
        # Note: 'row' is a reserved keyword in MySQL, so we need to escape it with backticks
        with connections[db_connection].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    r.id, r.title, r.description, r.likelihood, r.impact, r.score,
                    r.priority, r.ai_explanation, r.suggested_mitigations, r.status,
                    r.assigned_to, r.created_by, r.created_at, r.updated_at,
                    r.acknowledged_at, r.mitigated_at, r.exposure_rating, r.risk_type,
                    r.entity, r.data, r.`row`
                FROM risk_tprm r
                LEFT JOIN temp_vendor tv ON r.`row` = CAST(tv.id AS CHAR)
                WHERE r.entity = 'vendor_management'
                AND r.`row` = %s
                AND tv.TenantId = %s
                ORDER BY r.created_at DESC
            """, [str(vendor_id), tenant_id])

            columns = [col[0] for col in cursor.description]
            risk_rows = cursor.fetchall()

            print(f"Debug - Querying risks for vendor {vendor_id} with entity='vendor_management' and row='{vendor_id}'")
            print(f"Debug - Found {len(risk_rows)} internal risks")

            internal_risk_list = []
            for row in risk_rows:
                risk_dict = dict(zip(columns, row))
                risk_data = {
                    'id': risk_dict.get('id'),
                    'vendor_id': risk_dict.get('row'),  # Using row field as vendor_id
                    'title': risk_dict.get('title', ''),
                    'description': risk_dict.get('description', ''),
                    'likelihood': risk_dict.get('likelihood'),
                    'impact': risk_dict.get('impact'),
                    'score': risk_dict.get('score'),
                    'priority': risk_dict.get('priority', ''),
                    'ai_explanation': risk_dict.get('ai_explanation', ''),
                    'suggested_mitigations': risk_dict.get('suggested_mitigations'),
                    'status': risk_dict.get('status', ''),
                    'assigned_to': risk_dict.get('assigned_to'),
                    'created_by': risk_dict.get('created_by'),
                    'created_at': risk_dict.get('created_at').isoformat() if risk_dict.get('created_at') else None,
                    'updated_at': risk_dict.get('updated_at').isoformat() if risk_dict.get('updated_at') else None,
                    'acknowledged_at': risk_dict.get('acknowledged_at').isoformat() if risk_dict.get('acknowledged_at') else None,
                    'mitigated_at': risk_dict.get('mitigated_at').isoformat() if risk_dict.get('mitigated_at') else None,
                    'exposure_rating': risk_dict.get('exposure_rating'),
                    'risk_type': risk_dict.get('risk_type', ''),
                    'entity': risk_dict.get('entity', ''),
                    'data': risk_dict.get('data', '')
                }
                internal_risk_list.append(risk_data)

        

        # Get external risks from screening results with ESCALATED status
        # MULTI-TENANCY: Filter by tenant through vendor
        external_risk_list = []
        
        with connections[db_connection].cursor() as cursor:
            # Get screening results and matches with ESCALATED status, filtered by tenant
            cursor.execute("""
                SELECT 
                    sm.match_id, esr.screening_id, esr.vendor_id, esr.screening_type,
                    esr.screening_date, sm.match_type, sm.match_score, sm.match_details,
                    sm.resolution_status, sm.resolution_notes, esr.search_terms,
                    esr.total_matches, esr.high_risk_matches, sm.is_false_positive,
                    sm.resolved_by, sm.resolved_date, esr.last_updated, esr.reviewed_by,
                    esr.review_date, esr.review_comments
                FROM external_screening_results esr
                INNER JOIN screening_matches sm ON esr.screening_id = sm.screening_id
                INNER JOIN temp_vendor tv ON esr.vendor_id = tv.id
                WHERE esr.vendor_id = %s
                AND sm.resolution_status = 'ESCALATED'
                AND tv.TenantId = %s
                ORDER BY esr.screening_date DESC
            """, [vendor_id, tenant_id])
            
            columns = [col[0] for col in cursor.description]
            match_rows = cursor.fetchall()
            
            for row in match_rows:
                match_dict = dict(zip(columns, row))
                external_risk = {
                    'match_id': match_dict.get('match_id'),
                    'screening_id': match_dict.get('screening_id'),
                    'vendor_id': match_dict.get('vendor_id'),
                    'screening_type': match_dict.get('screening_type', ''),
                    'screening_date': match_dict.get('screening_date').isoformat() if match_dict.get('screening_date') else None,
                    'match_type': match_dict.get('match_type', ''),
                    'match_score': float(match_dict.get('match_score')) if match_dict.get('match_score') else None,
                    'match_details': match_dict.get('match_details'),
                    'resolution_status': match_dict.get('resolution_status', ''),
                    'resolution_notes': match_dict.get('resolution_notes', ''),
                    'search_terms': match_dict.get('search_terms'),
                    'total_matches': match_dict.get('total_matches', 0),
                    'high_risk_matches': match_dict.get('high_risk_matches', 0),
                    'is_false_positive': match_dict.get('is_false_positive', False),
                    'resolved_by': match_dict.get('resolved_by'),
                    'resolved_date': match_dict.get('resolved_date').isoformat() if match_dict.get('resolved_date') else None,
                    'last_updated': match_dict.get('last_updated').isoformat() if match_dict.get('last_updated') else None,
                    'reviewed_by': match_dict.get('reviewed_by'),
                    'review_date': match_dict.get('review_date').isoformat() if match_dict.get('review_date') else None,
                    'review_comments': match_dict.get('review_comments', '')
                }
                external_risk_list.append(external_risk)

        

        # Combine risks for legacy compatibility

        all_risks = internal_risk_list.copy()  # Start with internal risks for backward compatibility

        

        # Calculate risk summary

        risk_summary = {

            'total_risks': len(internal_risk_list) + len(external_risk_list),

            'internal_risks_count': len(internal_risk_list),

            'external_risks_count': len(external_risk_list),

            'high_priority': len([r for r in internal_risk_list if r['priority'] and r['priority'].upper() in ['HIGH', 'CRITICAL']]),

            'medium_priority': len([r for r in internal_risk_list if r['priority'] and r['priority'].upper() == 'MEDIUM']),

            'low_priority': len([r for r in internal_risk_list if r['priority'] and r['priority'].upper() == 'LOW']),

            'open_risks': len([r for r in internal_risk_list if r['status'] and r['status'].upper() in ['OPEN', 'ACTIVE', 'IDENTIFIED']]),

            'mitigated_risks': len([r for r in internal_risk_list if r['status'] and r['status'].upper() in ['MITIGATED', 'CLOSED', 'RESOLVED']]),

            'escalated_external': len(external_risk_list)

        }

        

        print(f"Debug - Vendor {vendor_id}: {len(internal_risk_list)} internal risks, {len(external_risk_list)} external risks")

        

        # Additional debug info for internal risks
        if len(internal_risk_list) > 0:
            print(f"Debug - Internal risks found:")
            for risk in internal_risk_list:
                print(f"  - Risk ID: {risk.get('id')}, Title: {risk.get('title')}, Priority: {risk.get('priority')}, Status: {risk.get('status')}")
        else:
            print(f"Debug - No internal risks found for vendor {vendor_id}")
            
            # Check if there are any risks with different entity values using raw SQL
            # Note: 'row' is a reserved keyword in MySQL, so we need to escape it with backticks
            with connections[db_connection].cursor() as debug_cursor:
                debug_cursor.execute("""
                    SELECT COUNT(*) as total
                    FROM risk_tprm
                    WHERE `row` = %s
                """, [str(vendor_id)])
                count_row = debug_cursor.fetchone()
                total_count = count_row[0] if count_row else 0
                print(f"Debug - Total risks for vendor {vendor_id} (any entity): {total_count}")
                
                debug_cursor.execute("""
                    SELECT id, entity, title
                    FROM risk_tprm
                    WHERE `row` = %s
                    LIMIT 10
                """, [str(vendor_id)])
                debug_risks = debug_cursor.fetchall()
                for risk_row in debug_risks:
                    print(f"  - Risk ID: {risk_row[0]}, Entity: {risk_row[1]}, Title: {risk_row[2]}")

        

        return Response({

            'vendor_id': vendor_id,

            'risks': all_risks,  # For backward compatibility

            'internal_risks': internal_risk_list,

            'external_risks': external_risk_list,

            'screening_risks': external_risk_list,  # Alternative name for frontend compatibility

            'count': len(all_risks),

            'total_count': len(internal_risk_list) + len(external_risk_list),

            'risk_summary': risk_summary

        }, status=status.HTTP_200_OK)

        

    except Exception as e:

        print(f"Error fetching vendor risks for vendor {vendor_id}: {str(e)}")

        import traceback

        traceback.print_exc()

        return Response({

            'error': 'Failed to fetch vendor risks',

            'details': str(e),

            'vendor_id': vendor_id,

            'risks': [],

            'internal_risks': [],

            'external_risks': [],

            'screening_risks': [],

            'count': 0,

            'total_count': 0,

            'risk_summary': {

                'total_risks': 0,

                'internal_risks_count': 0,

                'external_risks_count': 0,

                'high_priority': 0,

                'medium_priority': 0,

                'low_priority': 0,

                'open_risks': 0,

                'mitigated_risks': 0,

                'escalated_external': 0

            }

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_submitted_questionnaire_assignments(request):

    """Get all questionnaire assignments with RESPONDED status for response approval
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        # MULTI-TENANCY: Filter assignments by tenant through temp_vendor
        assignments = QuestionnaireAssignments.objects.filter(

            status='RESPONDED',
            
            temp_vendor__tenant_id=tenant_id

        ).select_related(

            'temp_vendor',

            'questionnaire',

            'assigned_by'

        ).prefetch_related(

            'responses__question'

        ).order_by('-submission_date')

        

        assignment_data = []

        for assignment in assignments:

            # Get all questions and responses for this assignment

            questions_and_responses = []

            responses = QuestionnaireResponseSubmissions.objects.filter(

                assignment=assignment

            ).select_related('question').order_by('question__display_order')

            

            for response in responses:

                questions_and_responses.append({

                    'question_id': response.question.question_id,

                    'question_text': response.question.question_text,

                    'question_type': response.question.question_type,

                    'question_category': response.question.question_category,

                    'display_order': response.question.display_order,

                    'is_required': response.question.is_required,

                    'help_text': response.question.help_text,

                    'scoring_weight': float(response.question.scoring_weight) if response.question.scoring_weight else 1.0,

                    'options': response.question.options,

                    'conditional_logic': response.question.conditional_logic,

                    'vendor_response': response.vendor_response,

                    'vendor_comment': response.vendor_comment,

                    'reviewer_comment': response.reviewer_comment,

                    'is_completed': response.is_completed,

                    'score': float(response.score) if response.score else None,

                    'file_uploads': response.file_uploads,

                    'response_created_at': response.created_at.isoformat() if response.created_at else None,

                    'response_updated_at': response.updated_at.isoformat() if response.updated_at else None

                })

            

            # Calculate response statistics

            total_questions = len(questions_and_responses)

            completed_questions = len([q for q in questions_and_responses if q['is_completed']])

            required_questions = len([q for q in questions_and_responses if q['is_required']])

            completed_required = len([q for q in questions_and_responses if q['is_required'] and q['is_completed']])

            

            assignment_data.append({

                'assignment_id': assignment.assignment_id,

                'questionnaire_id': assignment.questionnaire.questionnaire_id,

                'questionnaire_name': assignment.questionnaire.questionnaire_name,

                'questionnaire_type': assignment.questionnaire.questionnaire_type,

                'questionnaire_description': assignment.questionnaire.description,

                'questionnaire_version': assignment.questionnaire.version,

                'vendor_id': assignment.temp_vendor.id,

                'vendor_company_name': assignment.temp_vendor.company_name,

                'vendor_code': assignment.temp_vendor.vendor_code,

                'vendor_legal_name': assignment.temp_vendor.legal_name,

                'vendor_business_type': assignment.temp_vendor.business_type,

                'assigned_date': assignment.assigned_date.isoformat() if assignment.assigned_date else None,

                'due_date': assignment.due_date.isoformat() if assignment.due_date else None,

                'submission_date': assignment.submission_date.isoformat() if assignment.submission_date else None,

                'overall_score': float(assignment.overall_score) if assignment.overall_score else None,

                'status': assignment.status,

                'assigned_by': {

                    'id': assignment.assigned_by.userid if assignment.assigned_by else None,

                    'name': assignment.assigned_by.username if assignment.assigned_by else "Unknown"

                } if assignment.assigned_by else None,

                'notes': assignment.notes,

                'questions_and_responses': questions_and_responses,

                'response_statistics': {

                    'total_questions': total_questions,

                    'completed_questions': completed_questions,

                    'required_questions': required_questions,

                    'completed_required': completed_required,

                    'completion_percentage': round((completed_questions / total_questions) * 100, 1) if total_questions > 0 else 0,

                    'required_completion_percentage': round((completed_required / required_questions) * 100, 1) if required_questions > 0 else 0

                }

            })

        

        return Response({

            'success': True,

            'assignments': assignment_data,

            'total_count': len(assignment_data)

        }, status=status.HTTP_200_OK)

        

    except Exception as e:

        print(f"Error fetching submitted questionnaire assignments: {str(e)}")

        return Response({

            'error': 'Failed to fetch submitted questionnaire assignments',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('ReviewApproveResponses')
@require_tenant
@tenant_filter
def save_reviewer_scores(request):

    """Save reviewer scores for questionnaire responses
    MULTI-TENANCY: Ensures assignment belongs to tenant's vendor
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        data = request.data

        assignment_id = data.get('assignment_id')

        scores = data.get('scores', [])  # List of {question_id, score, reviewer_comment}

        reviewer_id = data.get('reviewer_id')

        

        if not assignment_id:

            return Response({

                'error': 'Assignment ID is required'

            }, status=status.HTTP_400_BAD_REQUEST)

        

        # Get the assignment
        # MULTI-TENANCY: Filter by tenant

        try:

            assignment = QuestionnaireAssignments.objects.get(assignment_id=assignment_id, temp_vendor__tenant_id=tenant_id)

        except QuestionnaireAssignments.DoesNotExist:

            return Response({

                'error': 'Assignment not found'

            }, status=status.HTTP_404_NOT_FOUND)

        

        # Check workflow type and approval_type to determine where to save scores
        
        workflow_type = None
        
        stage_id = None

        approval_id = None

        approval_type = None

        

        with connections['default'].cursor() as cursor:

            cursor.execute("""

                SELECT ar.approval_id, aw.workflow_type

                FROM approval_requests ar

                JOIN approval_workflows aw ON ar.workflow_id = aw.workflow_id

                WHERE JSON_EXTRACT(ar.request_data, '$.request_data.questionnaire_assignment_id') = %s

            """, [str(assignment_id)])

            

            result = cursor.fetchone()

            if result:

                approval_id, workflow_type = result

                

                # Get the current stage for this reviewer

                cursor.execute("""

                    SELECT stage_id

                    FROM approval_stages

                    WHERE approval_id = %s AND assigned_user_id = %s

                    LIMIT 1

                """, [approval_id, reviewer_id])

                

                stage_result = cursor.fetchone()

                if stage_result:

                    stage_id = stage_result[0]

        
        # If we found an approval_id, attempt to detect approval_type from approval_requests.request_data
        if approval_id:
            try:
                with connections['default'].cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT request_data
                        FROM approval_requests
                        WHERE approval_id = %s
                        """,
                        [approval_id],
                    )
                    approval_row = cursor.fetchone()

                    if approval_row and approval_row[0]:
                        try:
                            if isinstance(approval_row[0], str):
                                approval_request_data = json.loads(approval_row[0])
                            else:
                                approval_request_data = approval_row[0]
                        except Exception:
                            approval_request_data = {}

                        rd = approval_request_data.get("request_data", approval_request_data) or {}
                        raw_approval_type = rd.get("approval_type") or rd.get("request_data", {}).get("approval_type")
                        if raw_approval_type:
                            approval_type = str(raw_approval_type)
            except Exception as e:
                print(f"Warning - save_reviewer_scores: unable to extract approval_type for approval_id={approval_id}: {str(e)}")

        approval_type_normalized = approval_type.lower().replace(" ", "_") if approval_type else ""

        print(f"Debug - save_reviewer_scores: workflow_type={workflow_type}, approval_type={approval_type_normalized}, stage_id={stage_id}")

        

        with transaction.atomic():

            updated_responses = []

            total_score = 0

            total_weight = 0

            

            # For MULTI_PERSON + response_approval workflows, save scores ONLY in stage response_data
            # For other workflows (including MULTI_LEVEL), save to questionnaire_response_submissions
            
            if workflow_type == 'MULTI_PERSON' and approval_type_normalized == 'response_approval' and stage_id:

                print(f"Debug - MULTI_PERSON workflow: Saving scores to stage response_data only (stage_id={stage_id})")

                

                # Save scores to the stage's response_data field

                with connections['default'].cursor() as cursor:

                    # Get current response_data

                    cursor.execute("""

                        SELECT response_data

                        FROM approval_stages

                        WHERE stage_id = %s

                    """, [stage_id])

                    

                    stage_row = cursor.fetchone()

                    existing_response_data = {}

                    

                    if stage_row and stage_row[0]:

                        try:

                            if isinstance(stage_row[0], str):

                                existing_response_data = json.loads(stage_row[0])

                            else:

                                existing_response_data = stage_row[0]

                        except:

                            existing_response_data = {}

                    

                    # Prepare reviewer_scores in response_data

                    if 'reviewer_scores' not in existing_response_data:

                        existing_response_data['reviewer_scores'] = {}

                    

                    # Add/update scores

                    for score_data in scores:

                        question_id = str(score_data.get('question_id'))

                        score = score_data.get('score')

                        reviewer_comment = score_data.get('reviewer_comment', '')

                        

                        if not question_id:

                            continue

                        

                        existing_response_data['reviewer_scores'][question_id] = {

                            'score': score,

                            'comment': reviewer_comment

                        }

                        

                        updated_responses.append(question_id)

                    

                    # Save back to stage

                    cursor.execute("""

                        UPDATE approval_stages

                        SET response_data = %s, updated_at = %s

                        WHERE stage_id = %s

                    """, [json.dumps(existing_response_data), timezone.now(), stage_id])

                    

                    connection.commit()

                    

                print(f"Debug - Saved {len(updated_responses)} scores to stage response_data for MULTI_PERSON workflow")

                

            else:

                # For non-MULTI_PERSON workflows, save directly to questionnaire_response_submissions

                print(f"Debug - Non-MULTI_PERSON workflow: Saving scores to questionnaire_response_submissions")

                

                for score_data in scores:

                    question_id = score_data.get('question_id')

                    score = score_data.get('score')

                    reviewer_comment = score_data.get('reviewer_comment', '')

                    

                    if not question_id:

                        continue

                    

                    try:

                        # Get the response submission

                        response = QuestionnaireResponseSubmissions.objects.get(

                            assignment=assignment,

                            question_id=question_id

                        )

                        

                        # Update the score and reviewer comment

                        if score is not None:

                            response.score = score

                            total_score += float(score) * float(response.question.scoring_weight)

                            total_weight += float(response.question.scoring_weight)

                        

                        if reviewer_comment:

                            response.reviewer_comment = reviewer_comment

                        

                        response.save()

                        updated_responses.append(response.response_id)

                        

                    except QuestionnaireResponseSubmissions.DoesNotExist:

                        continue

                    except Exception as e:

                        print(f"Error updating response for question {question_id}: {str(e)}")

                        continue

            

            # DO NOT calculate overall score during reviewer scoring

            # Overall score will only be calculated when final decision is made

            # Keep overall_score as 0 or null until final decision

            

            # Update the approval_requests table's request_data with reviewer scores

            # For MULTI_PERSON workflows, this will aggregate scores from stage response_data

            try:

                with connections['default'].cursor() as cursor:

                    # Get the approval_id associated with this assignment

                    cursor.execute("""

                        SELECT ar.approval_id, ar.request_data 

                        FROM approval_requests ar 

                        WHERE JSON_EXTRACT(ar.request_data, '$.request_data.questionnaire_assignment_id') = %s

                    """, [str(assignment_id)])

                    

                    result = cursor.fetchone()

                    if result:

                        approval_id, request_data = result

                        

                        # Parse the existing request_data

                        if isinstance(request_data, str):

                            request_data_obj = json.loads(request_data)

                        else:

                            request_data_obj = request_data

                        

                        # Update questions_and_responses with AVERAGE scores from all reviewers

                        # For MULTI_PERSON: read from stage response_data

                        # For MULTI_LEVEL: read from questionnaire_response_submissions

                        if 'request_data' in request_data_obj:

                            rd = request_data_obj['request_data']

                            if 'questions_and_responses' in rd:

                                print(f"Debug - Calculating AVERAGE scores for {len(rd['questions_and_responses'])} questions (workflow: {workflow_type})")

                                

                                # Get all stages for this approval to calculate average scores

                                cursor.execute("""

                                    SELECT stage_id, stage_name, assigned_user_name, response_data, stage_status

                                    FROM approval_stages

                                    WHERE approval_id = %s AND stage_status IN ('APPROVED', 'IN_PROGRESS')

                                    ORDER BY stage_order

                                """, [approval_id])

                                

                                stages_data = cursor.fetchall()

                                print(f"Debug - Found {len(stages_data)} stages for average calculation")

                                

                                # Calculate average scores for each question

                                question_averages = {}

                                

                                for stage_row in stages_data:

                                    stage_id, stage_name, user_name, response_data, stage_status = stage_row

                                    

                                    if response_data:

                                        try:

                                            if isinstance(response_data, str):

                                                stage_response = json.loads(response_data)

                                            else:

                                                stage_response = response_data

                                            

                                            # Extract reviewer scores from this stage

                                            reviewer_scores = stage_response.get('reviewer_scores', {})

                                            print(f"Debug - Stage {stage_name} ({user_name}) reviewer_scores: {reviewer_scores}")

                                            

                                            # Process each question score from this reviewer

                                            for question_id, score_data in reviewer_scores.items():

                                                question_id_str = str(question_id)

                                                score_value = score_data.get('score')

                                                

                                                if score_value is not None:

                                                    if question_id_str not in question_averages:

                                                        question_averages[question_id_str] = {

                                                            'scores': [],

                                                            'comments': [],

                                                            'reviewers': []

                                                        }

                                                    

                                                    question_averages[question_id_str]['scores'].append(float(score_value))

                                                    question_averages[question_id_str]['comments'].append(score_data.get('comment', ''))

                                                    question_averages[question_id_str]['reviewers'].append(user_name)

                                                    

                                        except Exception as e:

                                            print(f"Debug - Error processing stage {stage_id}: {str(e)}")

                                            continue

                                

                                print(f"Debug - Question averages calculated: {question_averages}")

                                

                                # Update each question with its AVERAGE score

                                for qr in rd['questions_and_responses']:

                                    question_id = str(qr.get('question_id'))

                                    

                                    if question_id in question_averages:

                                        scores_list = question_averages[question_id]['scores']

                                        if scores_list:

                                            # Calculate average score

                                            average_score = sum(scores_list) / len(scores_list)

                                            qr['score'] = round(average_score, 2)

                                            

                                            # Combine all reviewer comments

                                            all_comments = [c for c in question_averages[question_id]['comments'] if c.strip()]

                                            qr['reviewer_comment'] = '; '.join(all_comments) if all_comments else ''

                                            

                                            print(f"Debug - Updated Q{question_id}: average_score={qr['score']} (from {len(scores_list)} reviewers), comment={qr['reviewer_comment']}")

                                        else:

                                            print(f"Debug - No scores found for Q{question_id}")

                                    else:

                                        print(f"Debug - No average data for Q{question_id}")

                                

                                print(f"Debug - AVERAGE scores updated in request_data")

                        

                        # Update the request_data in the database

                        cursor.execute("""

                            UPDATE approval_requests 

                            SET request_data = %s, updated_at = %s 

                            WHERE approval_id = %s

                        """, [json.dumps(request_data_obj), timezone.now(), approval_id])

                        

                        connection.commit()

                        

                        print(f"Updated approval request {approval_id} with reviewer scores")

                        print(f"Questions updated with reviewer scores: {len(scores)}")

                        

            except Exception as e:

                print(f"Error updating approval request with reviewer scores: {str(e)}")

                # Don't fail the entire operation if this update fails

        

        return Response({

            'success': True,

            'message': 'Reviewer scores saved successfully',

            'updated_responses': updated_responses,

            'overall_score': None  # No overall score calculated during reviewer scoring

        }, status=status.HTTP_200_OK)

        

    except Exception as e:

        print(f"Error saving reviewer scores: {str(e)}")

        return Response({

            'error': 'Failed to save reviewer scores',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('update_vendor')
@require_tenant
@tenant_filter
def save_stage_draft(request):

    """Save draft decision for an approval stage
    MULTI-TENANCY: Ensures stage belongs to tenant's vendor
    """

    try:

        data = request.data

        stage_id = data.get('stage_id')

        draft_data = data.get('draft_data', {})

        user_id = data.get('user_id')

        

        if not stage_id:

            return Response({

                'error': 'Stage ID is required'

            }, status=status.HTTP_400_BAD_REQUEST)

        

        with connections['default'].cursor() as cursor:

            # Check if stage exists and is assigned to user

            cursor.execute("""

                SELECT approval_id, stage_name, stage_status, assigned_user_id, response_data

                FROM approval_stages 

                WHERE stage_id = %s

            """, [stage_id])

            

            stage_row = cursor.fetchone()

            if not stage_row:

                return Response({

                    'error': 'Stage not found'

                }, status=status.HTTP_404_NOT_FOUND)

            

            approval_id, stage_name, stage_status, assigned_user_id, existing_response_data = stage_row

            

            # Merge existing response data with new draft data

            existing_data = {}

            if existing_response_data:

                try:

                    if isinstance(existing_response_data, str):

                        existing_data = json.loads(existing_response_data)

                    else:

                        existing_data = existing_response_data

                except json.JSONDecodeError:

                    existing_data = {}

            

            # Merge draft data with existing data

            merged_data = {**existing_data, **draft_data}

            

            # Standardize the response data structure

            standardized_data = standardize_response_data(

                response_data=merged_data,

                stage_status=stage_status,

                decision=merged_data.get('decision', ''),

                comments=merged_data.get('comments', ''),

                rejection_reason=merged_data.get('rejection_reason', '')

            )

            

            # Mark as draft

            standardized_data['is_draft'] = True

            standardized_data['draft_saved_at'] = timezone.now().isoformat()

            standardized_data['draft_saved_by'] = user_id

            

            # Update the stage with standardized draft data

            cursor.execute("""

                UPDATE approval_stages 

                SET response_data = %s, updated_at = %s

                WHERE stage_id = %s

            """, [

                json.dumps(standardized_data),

                timezone.now(),

                stage_id

            ])

        

        return Response({

            'success': True,

            'message': 'Draft saved successfully',

            'stage_id': stage_id,

            'merged_data_keys': list(merged_data.keys())

        }, status=status.HTTP_200_OK)

        

    except Exception as e:

        print(f"Error saving stage draft: {str(e)}")

        return Response({

            'error': 'Failed to save draft',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def load_stage_draft(request, stage_id):

    """Load saved draft decision for an approval stage
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        user_id = request.query_params.get('user_id')

        # Use tprm database connection for vendor approval queries
        import logging
        from django.db import connections as db_connections
        logger = logging.getLogger(__name__)
        
        # Use tprm connection if available, otherwise fall back to default
        if 'tprm' in db_connections.databases:
            db_connection = db_connections['tprm']
            db_name = db_connection.settings_dict.get('NAME', 'tprm_integration')
            logger.info(f"[Load Stage Draft] Using tprm database connection: {db_name} for stage_id: {stage_id}")
        else:
            db_connection = db_connections['default']
            db_name = db_connection.settings_dict.get('NAME', '')
            logger.warning(f"[Load Stage Draft] tprm connection not found, using default: {db_name}")

        with db_connection.cursor() as cursor:
            # Check if temp_vendor table exists
            cursor.execute("SHOW TABLES LIKE 'temp_vendor'")
            temp_vendor_exists = cursor.fetchone() is not None

            # Get the stage with draft data
            # MULTI-TENANCY: Filter by tenant
            if temp_vendor_exists:
                cursor.execute("""

                    SELECT ast.approval_id, ast.stage_name, ast.stage_status, ast.assigned_user_id, ast.response_data

                    FROM approval_stages ast

                    JOIN approval_requests ar ON ast.approval_id = ar.approval_id
                    
                    LEFT JOIN temp_vendor tv ON JSON_EXTRACT(ar.request_data, '$.vendor_id') = tv.id

                    WHERE ast.stage_id = %s
                    
                    AND (tv.TenantId = %s OR tv.TenantId IS NULL)

                """, [stage_id, tenant_id])
            else:
                # If temp_vendor doesn't exist, query without tenant filtering via temp_vendor
                cursor.execute("""

                    SELECT ast.approval_id, ast.stage_name, ast.stage_status, ast.assigned_user_id, ast.response_data

                    FROM approval_stages ast

                    JOIN approval_requests ar ON ast.approval_id = ar.approval_id

                    WHERE ast.stage_id = %s

                """, [stage_id])

            

            stage_row = cursor.fetchone()

            if not stage_row:

                return Response({

                    'error': 'Stage not found'

                }, status=status.HTTP_404_NOT_FOUND)

            

            approval_id, stage_name, stage_status, assigned_user_id, response_data = stage_row

            

            # Parse draft data

            draft_data = {}

            if response_data:

                try:

                    if isinstance(response_data, str):

                        draft_data = json.loads(response_data)

                    else:

                        draft_data = response_data

                except json.JSONDecodeError:

                    draft_data = {}

            

            return Response({

                'success': True,

                'draft_data': draft_data,

                'stage_id': stage_id,

                'stage_name': stage_name,

                'stage_status': stage_status

            }, status=status.HTTP_200_OK)

        

    except Exception as e:

        print(f"Error loading stage draft: {str(e)}")

        return Response({

            'error': 'Failed to load draft',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_parallel_approval_scoring_data(request, approval_id):

    """Get aggregated scoring data for parallel response approval workflows
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        # Use tprm database connection for queries involving temp_vendor
        # temp_vendor table is in tprm_integration database, not grc2
        from django.db import connections as db_connections
        import logging
        logger = logging.getLogger(__name__)
        
        # Use tprm connection if available, otherwise fall back to default
        if 'tprm' in db_connections.databases:
            db_connection = db_connections['tprm']
            db_name = db_connection.settings_dict.get('NAME', 'tprm_integration')
            logger.info(f"[Parallel Scoring] Using tprm database connection: {db_name} for approval_id: {approval_id}")
        else:
            db_connection = db_connections['default']
            db_name = db_connection.settings_dict.get('NAME', '')
            logger.warning(f"[Parallel Scoring] tprm connection not found, using default: {db_name}")

        with db_connection.cursor() as cursor:

            # Get the approval request and verify it's a parallel response approval
            # MULTI-TENANCY: Filter by tenant
            # Note: temp_vendor is in tprm_integration database, so we use tprm connection

            cursor.execute("""

                SELECT ar.approval_id, ar.request_data, aw.workflow_type

                FROM approval_requests ar

                JOIN approval_workflows aw ON ar.workflow_id = aw.workflow_id
                
                LEFT JOIN temp_vendor tv ON JSON_EXTRACT(ar.request_data, '$.vendor_id') = tv.id

                WHERE ar.approval_id = %s

                AND (tv.TenantId = %s OR tv.TenantId IS NULL)

            """, [approval_id, tenant_id])

            

            request_row = cursor.fetchone()

            if not request_row:

                return Response({

                    'error': 'Approval request not found'

                }, status=status.HTTP_404_NOT_FOUND)

            

            approval_id, request_data, workflow_type = request_row

            

            # Parse request data to check if it's response approval

            try:

                if isinstance(request_data, str):

                    request_data_obj = json.loads(request_data)

                else:

                    request_data_obj = request_data

            except:

                request_data_obj = {}

            

            rd = request_data_obj.get('request_data', request_data_obj)

            if rd.get('approval_type') != 'response_approval':

                return Response({

                    'error': 'This endpoint is only for response approval workflows'

                }, status=status.HTTP_400_BAD_REQUEST)

            

            # Get assignment data

            assignment_id = rd.get('questionnaire_assignment_id')

            if not assignment_id:

                return Response({

                    'error': 'Assignment ID not found in request data'

                }, status=status.HTTP_400_BAD_REQUEST)

            

            # Get assignment details

            assignment = QuestionnaireAssignments.objects.select_related(

                'temp_vendor', 'questionnaire', 'assigned_by'

            ).get(assignment_id=assignment_id)

            

            # Get all stages for this approval
            # Note: weightage column doesn't exist in approval_stages table, so it's not selected
            # Join with users table to get proper user names in case assigned_user_name is NULL

            cursor.execute("""

                SELECT 
                    ast.stage_id, 
                    ast.stage_name, 
                    ast.assigned_user_id, 
                    COALESCE(
                        NULLIF(TRIM(ast.assigned_user_name), ''), 
                        u.UserName, 
                        CONCAT(u.FirstName, ' ', u.LastName),
                        u.FirstName,
                        CAST(ast.assigned_user_id AS CHAR),
                        'Unknown Reviewer'
                    ) as assigned_user_name, 
                    ast.stage_status, 
                    ast.response_data, 
                    ast.completed_at
                
                FROM approval_stages ast
                LEFT JOIN users u ON ast.assigned_user_id = u.UserId
                
                WHERE ast.approval_id = %s
                
                ORDER BY ast.stage_order

            """, [approval_id])
            
            print(f"Debug - Fetching stages for approval_id: {approval_id}")

            

            stages = []

            all_reviewer_scores = {}

            

            for stage_row in cursor.fetchall():

                stage_id, stage_name, user_id, user_name, stage_status, response_data, completed_at = stage_row
                
                # weightage column doesn't exist in approval_stages table, so set to None
                weightage = None

                
                # Debug logging
                print(f"Debug - Stage: {stage_id}, UserID: {user_id}, UserName: '{user_name}', Status: {stage_status}")

                stage_data = {

                    'stage_id': stage_id,

                    'stage_name': stage_name,

                    'assigned_user_id': user_id,

                    'assigned_user_name': user_name if user_name and user_name.strip() else f'User {user_id}',

                    'stage_status': stage_status,

                    # Raw influence value entered as "weightage" for this reviewer (may be null)
                    'weightage': float(weightage) if weightage is not None else None,

                    'completed_at': completed_at.isoformat() if completed_at else None,

                    'reviewer_scores': {}

                }

                

                # Parse response data to get reviewer scores

                if response_data:

                    try:

                        if isinstance(response_data, str):

                            rd_obj = json.loads(response_data)

                        else:

                            rd_obj = response_data

                        

                        # Debug: Log the response data structure

                        print(f"Debug - Stage {stage_id} ({user_name}) response_data:", rd_obj)

                        

                        # Extract reviewer scores from different possible formats

                        reviewer_scores = {}

                        

                        # Format 1: Direct reviewer_scores object (for rejected/draft stages)

                        if rd_obj.get('reviewer_scores'):

                            reviewer_scores = rd_obj['reviewer_scores']

                        

                        # Format 2: Check if scores are stored in a different structure

                        # Look for question-specific scores in the response data

                        for key, value in rd_obj.items():

                            if isinstance(value, dict) and 'score' in value:

                                # This might be a question score

                                reviewer_scores[key] = value

                        

                        # Format 3: For approved stages, the data might be stored differently

                        # Check if there are any numeric keys that might be question IDs

                        for key, value in rd_obj.items():

                            if key.isdigit() and isinstance(value, (int, float)):

                                # This might be a question score stored directly

                                reviewer_scores[key] = {

                                    'score': value,

                                    'comment': ''

                                }

                            elif key.isdigit() and isinstance(value, dict) and 'score' in value:

                                # This is definitely a question score

                                reviewer_scores[key] = value

                        

                        # Format 4: Handle approved stages with different data structure

                        # Some approved stages might have the scores in a different format

                        if not reviewer_scores and stage_status == 'APPROVED':

                            # For approved stages, try to extract scores from the response data

                            for key, value in rd_obj.items():

                                if key.isdigit():

                                    # This is likely a question ID

                                    if isinstance(value, dict):

                                        reviewer_scores[key] = value

                                    elif isinstance(value, (int, float)):

                                        reviewer_scores[key] = {

                                            'score': value,

                                            'comment': rd_obj.get(f'{key}_comment', '')

                                        }

                        

                        if reviewer_scores:

                            stage_data['reviewer_scores'] = reviewer_scores

                            print(f"Debug - Found reviewer_scores for {user_name}:", reviewer_scores)

                            

                            # Aggregate scores across all reviewers

                            for question_id, score_data in reviewer_scores.items():

                                if question_id not in all_reviewer_scores:

                                    all_reviewer_scores[question_id] = []

                                

                                # Ensure score is properly converted to float

                                score_value = score_data.get('score')

                                if score_value is not None:

                                    try:

                                        score_value = float(score_value)

                                    except (ValueError, TypeError):

                                        score_value = 0

                                

                                all_reviewer_scores[question_id].append({

                                    'reviewer': user_name,

                                    'score': score_value,

                                    'comment': score_data.get('comment', ''),

                                    'stage_id': stage_id

                                })

                        else:

                            print(f"Debug - No reviewer_scores found for {user_name}")

                        

                        if rd_obj.get('total_score'):

                            stage_data['total_score'] = rd_obj['total_score']

                        

                    except json.JSONDecodeError:

                        pass

                

                stages.append(stage_data)

            

            # Get questions and responses from the assignment

            questions_and_responses = []

            responses = QuestionnaireResponseSubmissions.objects.filter(

                assignment=assignment

            ).select_related('question').order_by('question__display_order')

            

            for response in responses:

                # Get submitted scores for this question

                submitted_scores = all_reviewer_scores.get(str(response.question.question_id), [])

                

                # Create comprehensive reviewer scores list (all reviewers, including pending)

                comprehensive_reviewer_scores = []

                
                # Debug: Log stages info
                print(f"Debug - Building reviewer scores for question {response.question.question_id}")
                print(f"Debug - Available stages: {[(s['stage_id'], s['assigned_user_name'], s.get('weightage')) for s in stages]}")

                for stage in stages:

                    # Find if this reviewer has submitted a score

                    submitted_score = next(

                        (score for score in submitted_scores if score['stage_id'] == stage['stage_id']), 

                        None

                    )

                    

                    if submitted_score:

                        # Reviewer has submitted - use their actual score
                        
                        reviewer_entry = {

                            'stage_id': stage['stage_id'],

                            'reviewer': stage['assigned_user_name'],

                            'reviewer_id': stage['assigned_user_id'],

                            'weightage': stage.get('weightage'),  # Include raw influence weight

                            'score': submitted_score['score'],

                            'comment': submitted_score['comment'],

                            'decision': stage['stage_status'] if stage['stage_status'] in ['APPROVED', 'REJECTED'] else 'REVIEWED',

                            'completed_at': stage['completed_at']

                        }
                        
                        print(f"Debug - Added reviewer (submitted): {reviewer_entry['reviewer']} (ID: {reviewer_entry['reviewer_id']}) with score {reviewer_entry['score']}")
                        
                        comprehensive_reviewer_scores.append(reviewer_entry)

                    else:

                        # Reviewer hasn't submitted yet - show as pending

                        comprehensive_reviewer_scores.append({

                            'stage_id': stage['stage_id'],

                            'reviewer': stage['assigned_user_name'],

                            'reviewer_id': stage['assigned_user_id'],

                            'weightage': stage.get('weightage'),  # Include raw influence weight

                            'score': None,

                            'comment': '',

                            'decision': 'PENDING' if stage['stage_status'] == 'PENDING' else stage['stage_status'],

                            'completed_at': stage['completed_at']

                        })

                

                # Calculate weighted score using exponent-based normalization from weightage column

                submitted_scores_only = [score for score in comprehensive_reviewer_scores if score['score'] is not None]

                average_score = 0

                

                if submitted_scores_only:

                    scoring_weight = float(response.question.scoring_weight) if response.question.scoring_weight else 1.0

                    max_score_for_question = scoring_weight * 10  # Max score = weight * 10

                    

                    # Extract valid scores AND their raw influence weights (weightage)

                    valid_scores = []

                    raw_influences = []

                    

                    for score_entry in submitted_scores_only:

                        try:

                            score_val = float(score_entry['score'])

                            valid_scores.append(score_val)

                            

                            # Get the raw influence value (weightage) for this reviewer

                            stage_weight = score_entry.get('weightage')

                            raw_influences.append(stage_weight)

                            

                        except (ValueError, TypeError):

                            continue

                    

                    if valid_scores:

                        # Compute normalized weights using exponent-based formula: a^x + b^x + c^x = 10

                        weights = compute_exponent_normalized_weights(raw_influences)

                        

                        # Fallback to equal weights if computation fails

                        if not weights or len(weights) != len(valid_scores):

                            equal_w = 1.0 / len(valid_scores)

                            weights = [equal_w for _ in valid_scores]

                        

                        # Calculate weighted final score

                        weighted_score = sum(s * w for s, w in zip(valid_scores, weights))

                        

                        # Normalize to percentage scale (0-100)

                        average_score = (weighted_score / max_score_for_question) * 100 if max_score_for_question > 0 else 0

                        average_score = min(max(average_score, 0), 100.0)

                        

                        # Debug logging to see what's happening

                        print(f"Question {response.question.question_id} calculation (exponent-weighted):")

                        print(f"  Weight: {scoring_weight}, Max Score: {max_score_for_question}")

                        print(f"  Raw influences (weightage): {raw_influences}")

                        print(f"  Individual scores: {valid_scores}")

                        print(f"  Normalized weights (%): {[round(w*100.0, 2) for w in weights]}")

                        print(f"  Weighted score: {weighted_score:.2f}")

                        print(f"  Percentage (final): {average_score:.1f}%")

                

                questions_and_responses.append({

                    'question_id': response.question.question_id,

                    'question_text': response.question.question_text,

                    'question_type': response.question.question_type,

                    'question_category': response.question.question_category,

                    'display_order': response.question.display_order,

                    'is_required': response.question.is_required,

                    'scoring_weight': float(response.question.scoring_weight) if response.question.scoring_weight else 1.0,

                    'vendor_response': response.vendor_response,

                    'vendor_comment': response.vendor_comment,

                    'final_score': float(response.score) if response.score is not None else None,

                    'final_reviewer_comment': response.reviewer_comment,

                    'reviewer_scores': comprehensive_reviewer_scores,

                    'average_score': average_score

                })

            

            # Debug: Log the final aggregated scores

            print(f"Debug - Final all_reviewer_scores:", all_reviewer_scores)

            

            # Calculate overall statistics

            total_questions = len(questions_and_responses)

            questions_with_scores = len([q for q in questions_and_responses if q['reviewer_scores']])

            
            
            # Calculate a preview overall score from the weighted average_scores
            # This shows the assignee what the score would be if they used the calculated weighted scores
            
            preview_overall_score = 0.0
            
            if questions_and_responses:
                
                total_weighted_score = 0.0
                
                total_weighted_max = 0.0
                
                
                
                for qr in questions_and_responses:
                    
                    scoring_weight = qr['scoring_weight']
                    
                    max_score_for_question = scoring_weight * 10
                    
                    average_score_percentage = qr.get('average_score', 0)  # This is 0-100 percentage
                    
                    
                    
                    # Convert percentage back to actual score
                    
                    actual_score = (average_score_percentage / 100.0) * max_score_for_question
                    
                    
                    
                    total_weighted_score += actual_score
                    
                    total_weighted_max += max_score_for_question
                
                
                
                if total_weighted_max > 0:
                    
                    preview_overall_score = (total_weighted_score / total_weighted_max) * 100
                    
                    preview_overall_score = min(max(preview_overall_score, 0), 100.0)
                
                
                
                print(f"Debug - Preview overall score calculated: {preview_overall_score:.2f}%")
            
            
            
            # Use preview score if the assignment overall_score is 0 or None
            
            display_overall_score = assignment.overall_score if assignment.overall_score else preview_overall_score

            

            return Response({

                'success': True,

                'approval_id': approval_id,

                'workflow_type': workflow_type,

                'assignment': {

                    'assignment_id': assignment.assignment_id,

                    'vendor_company_name': assignment.temp_vendor.company_name,

                    'vendor_code': assignment.temp_vendor.vendor_code,

                    'questionnaire_name': assignment.questionnaire.questionnaire_name,

                    'questionnaire_type': assignment.questionnaire.questionnaire_type,

                    'overall_score': float(display_overall_score) if display_overall_score else 0.0,
                    
                    'preview_score': float(preview_overall_score) if preview_overall_score else 0.0,

                    'status': assignment.status

                },

                'stages': stages,

                'questions_and_responses': questions_and_responses,

                'statistics': {

                    'total_questions': total_questions,

                    'questions_with_scores': questions_with_scores,

                    'total_reviewers': len(stages),

                    'completed_reviews': len([s for s in stages if s['stage_status'] == 'APPROVED'])

                }

            }, status=status.HTTP_200_OK)

            

    except QuestionnaireAssignments.DoesNotExist:

        return Response({

            'error': 'Assignment not found'

        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:

        print(f"Error fetching parallel approval scoring data: {str(e)}")

        return Response({

            'error': 'Failed to fetch scoring data',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('update_vendor')
@require_tenant
@tenant_filter
def save_final_assignee_scores(request):

    """Save final scores made by assignee for parallel response approval
    MULTI-TENANCY: Ensures assignment belongs to tenant's vendor
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        data = request.data

        assignment_id = data.get('assignment_id')

        final_scores = data.get('final_scores', [])  # List of {question_id, final_score, final_comment}

        assignee_decision = data.get('assignee_decision')  # APPROVE/REJECT

        assignee_comments = data.get('assignee_comments', '')

        assignee_id = data.get('assignee_id')

        

        if not assignment_id:

            return Response({

                'error': 'Assignment ID is required'

            }, status=status.HTTP_400_BAD_REQUEST)

        

        if not assignee_decision or assignee_decision not in ['APPROVE', 'REJECT', 'DRAFT']:

            return Response({

                'error': 'Valid assignee decision (APPROVE/REJECT/DRAFT) is required'

            }, status=status.HTTP_400_BAD_REQUEST)

        

        # Get the assignment
        # MULTI-TENANCY: Filter by tenant

        try:

            assignment = QuestionnaireAssignments.objects.get(assignment_id=assignment_id, temp_vendor__tenant_id=tenant_id)

        except QuestionnaireAssignments.DoesNotExist:

            return Response({

                'error': 'Assignment not found'

            }, status=status.HTTP_404_NOT_FOUND)

        

        with transaction.atomic():

            # FIRST: Get workflow type to determine data source

            workflow_type = None

            with connection.cursor() as wf_cursor:

                wf_cursor.execute("""

                    SELECT aw.workflow_type

                    FROM approval_requests ar

                    JOIN approval_workflows aw ON ar.workflow_id = aw.workflow_id

                    WHERE JSON_EXTRACT(ar.request_data, '$.request_data.questionnaire_assignment_id') = %s

                """, [str(assignment_id)])

                

                wf_result = wf_cursor.fetchone()

                if wf_result:

                    workflow_type = wf_result[0]

            

            print(f"Debug - save_final_assignee_scores: workflow_type={workflow_type}, decision={assignee_decision}")

            

            # SECOND: Get all stages and calculate average scores for each question

            question_averages = {}  # Initialize outside the if block

            

            with connection.cursor() as avg_cursor:

                # Get all approved stages for this assignment

                avg_cursor.execute("""

                    SELECT ar.approval_id FROM approval_requests ar 

                    WHERE JSON_EXTRACT(ar.request_data, '$.request_data.questionnaire_assignment_id') = %s

                """, [str(assignment_id)])

                

                approval_result = avg_cursor.fetchone()

                if approval_result:

                    approval_id = approval_result[0]

                    

                    # Get all stages with scores (for MULTI_PERSON, scores are in stage response_data)

                    avg_cursor.execute("""

                        SELECT stage_id, stage_name, assigned_user_name, response_data, stage_status

                        FROM approval_stages

                        WHERE approval_id = %s AND stage_status = 'APPROVED'

                        ORDER BY stage_order

                    """, [approval_id])

                    

                    stages_data = avg_cursor.fetchall()

                    print(f"Debug - Found {len(stages_data)} approved stages for average calculation")

                    

                    # Calculate average scores for each question

                    for stage_row in stages_data:

                        stage_id, stage_name, user_name, response_data, stage_status = stage_row

                        

                        if response_data:

                            try:

                                if isinstance(response_data, str):

                                    stage_response = json.loads(response_data)

                                else:

                                    stage_response = response_data

                                

                                # Extract reviewer scores from this stage

                                reviewer_scores = stage_response.get('reviewer_scores', {})

                                print(f"Debug - Stage {stage_name} ({user_name}) reviewer_scores: {reviewer_scores}")

                                

                                # Process each question score from this reviewer

                                for question_id, score_data in reviewer_scores.items():

                                    question_id_str = str(question_id)

                                    score_value = score_data.get('score')

                                    

                                    if score_value is not None:

                                        if question_id_str not in question_averages:

                                            question_averages[question_id_str] = {

                                                'scores': [],

                                                'comments': []

                                            }

                                        

                                        question_averages[question_id_str]['scores'].append(float(score_value))

                                        question_averages[question_id_str]['comments'].append(score_data.get('comment', ''))

                                        

                            except Exception as e:

                                print(f"Debug - Error processing stage {stage_id}: {str(e)}")

                                continue

                    

                    print(f"Debug - Question averages calculated: {question_averages}")

                else:

                    print("Debug - No approval found for this assignment")

            

            # THIRD: Update individual question scores in database using calculated averages

            # For MULTI_PERSON workflows: Only write to questionnaire_response_submissions when APPROVED

            # For other workflows: Write immediately

            scores_to_use = {}

            

            # Use final_scores from the request if provided

            if final_scores:

                for score_data in final_scores:

                    question_id_str = str(score_data.get('question_id'))

                    if question_id_str:

                        scores_to_use[question_id_str] = {

                            'score': score_data.get('final_score'),

                            'comment': score_data.get('final_comment', '')

                        }

            

            # Fall back to calculated averages if no final scores provided

            if not scores_to_use:

                for question_id_str, avg_data in question_averages.items():

                    if avg_data['scores']:

                        average_score = sum(avg_data['scores']) / len(avg_data['scores'])

                        scores_to_use[question_id_str] = {

                            'score': round(average_score, 2),

                            'comment': '; '.join([c for c in avg_data['comments'] if c.strip()])

                        }

            

            # CRITICAL FIX: If no scores available at all, ensure all questions get a default score

            if not scores_to_use:

                print("Debug - No scores found, setting default scores for all questions")

                all_questions = QuestionnaireResponseSubmissions.objects.filter(

                    assignment=assignment

                ).select_related('question')

                

                for response in all_questions:

                    question_id_str = str(response.question.question_id)

                    # Set a default score based on scoring weight (50% of max score)

                    default_score = (float(response.question.scoring_weight) * 10) * 0.5

                    scores_to_use[question_id_str] = {

                        'score': round(default_score, 2),

                        'comment': 'Default score assigned (no reviewer scores available)'

                    }

                    print(f"Debug - Setting default score for Q{question_id_str}: {default_score}")

            

            print(f"Debug - Final scores_to_use: {scores_to_use}")

            

            # ALWAYS write the weighted scores to questionnaire_response_submissions
            # This ensures question-wise scores are persisted in the database for all workflows

            should_write_to_db = True  # Always save question-wise scores

            

            # Write the weighted/final scores to questionnaire_response_submissions

            print(f"Debug - Writing weighted question scores to questionnaire_response_submissions (workflow={workflow_type}, decision={assignee_decision})")

            

            # Update database with the final weighted scores

            for question_id_str, score_info in scores_to_use.items():

                try:

                    response = QuestionnaireResponseSubmissions.objects.get(

                        assignment=assignment,

                        question_id=int(question_id_str)

                    )

                    

                    # Save the weighted/final score for this question

                    response.score = score_info['score']

                    

                    # Save the assignee's final comment (or combined reviewer comments)

                    response.reviewer_comment = score_info['comment']

                    

                    response.save()

                    print(f"Debug - Saved weighted score to DB: Q{question_id_str} = {response.score}")

                    

                except QuestionnaireResponseSubmissions.DoesNotExist:

                    print(f"Warning - Response not found for question {question_id_str} in assignment {assignment_id}")

                    continue

                except Exception as e:

                    print(f"Error - Failed to save score for question {question_id_str}: {str(e)}")

                    continue

            

            # FOURTH: Calculate overall score from the database

            # Since we always write scores to questionnaire_response_submissions now, 

            # we can always calculate from the database

            total_weighted_score = 0

            total_weighted_max = 0

            

            # Scores are in database - fetch and calculate

            print(f"Debug - Calculating overall score from database")

            all_responses = QuestionnaireResponseSubmissions.objects.filter(

                assignment=assignment

            ).select_related('question')

            

            for response in all_responses:

                weight = float(response.question.scoring_weight) if response.question.scoring_weight else 1.0

                max_score = weight * 10

                

                # Use the weighted score from database (which was just updated)

                if response.score is not None:

                    actual_score = float(response.score)

                    total_weighted_score += actual_score

                    total_weighted_max += max_score

                    

                    # Debug logging

                    print(f"Score calculation - Q{response.question.question_id}: {actual_score}/{max_score} (weight: {weight})")

                else:

                    # If score is still None, add to max but not to total

                    total_weighted_max += max_score

                    print(f"Score calculation - Q{response.question.question_id}: No score found, adding to max only")

            

            # Calculate and update overall score in questionnaire_assignments table

            if total_weighted_max > 0:

                overall_score = (total_weighted_score / total_weighted_max) * 100

                # Ensure score doesn't exceed 100

                overall_score = min(overall_score, 100.0)

                assignment.overall_score = round(overall_score, 2)

                

                # Debug logging for overall score calculation

                print(f"Overall score calculation:")

                print(f"  Total weighted score: {total_weighted_score}")

                print(f"  Total weighted max: {total_weighted_max}")

                print(f"  Overall percentage: {overall_score:.2f}%")

            else:

                # If no scores available, set to 0

                assignment.overall_score = 0.0

            

            # Update assignment status based on decision

            if assignee_decision == 'APPROVE':

                assignment.status = 'APPROVED'

                assignment.completion_date = timezone.now()

            elif assignee_decision == 'REJECT':

                assignment.status = 'REJECTED'

                assignment.completion_date = timezone.now()

            # For DRAFT, don't change the status or completion date

            

            # Update notes with assignee decision

            assignee_notes = f"Final Decision: {assignee_decision}"

            if assignee_comments:

                assignee_notes += f"\nAssignee Comments: {assignee_comments}"

            

            if assignment.notes:

                assignment.notes += f"\n\n{assignee_notes}"

            else:

                assignment.notes = assignee_notes

            

            # FOURTH: Save the questionnaire_assignments table with updated overall_score

            assignment.save()

            print(f"Debug - Saved assignment {assignment_id} with overall_score: {assignment.overall_score}")

            

            # LIFECYCLE TRACKING: Complete Response Approval stage when assignee approves
            if assignee_decision == 'APPROVE' and assignment.temp_vendor:
                try:
                    vendor_id = assignment.temp_vendor.id
                    print(f"Debug - Assignee APPROVED response for vendor {vendor_id}, completing Response Approval lifecycle stage")
                    _end_response_approval_start_vendor_approval(vendor_id)
                    print(f"✓ Response Approval lifecycle stage completed for vendor {vendor_id} after assignee approval")
                except Exception as e:
                    print(f"ERROR - Failed to update lifecycle stage after assignee approval: {str(e)}")
                    import traceback
                    traceback.print_exc()

            

            # Update the approval_requests table's request_data with scoring information
            # CRITICAL: Store approval_id outside the if block so version creation can access it
            approval_id_for_version = None
            request_data_for_version = None

            try:

                with connections['default'].cursor() as cursor:

                    # Get the approval_id associated with this assignment

                    cursor.execute("""

                        SELECT ar.approval_id, ar.request_data 

                        FROM approval_requests ar 

                        WHERE JSON_EXTRACT(ar.request_data, '$.request_data.questionnaire_assignment_id') = %s

                    """, [str(assignment_id)])

                    

                    result = cursor.fetchone()

                    

                    if not result:

                        print(f"❌ ERROR - No approval found for assignment {assignment_id} using JSON_EXTRACT")

                        print(f"❌ Trying alternative query method (LIKE)...")

                        # Try alternative query without JSON_EXTRACT

                        cursor.execute("""

                            SELECT ar.approval_id, ar.request_data 

                            FROM approval_requests ar 

                            WHERE ar.request_data LIKE %s

                        """, [f'%{assignment_id}%'])

                        result = cursor.fetchone()

                        

                        if not result:

                            print(f"❌ LIKE query failed. Trying third method via questionnaire_responses...")
                            
                            # Third method: Join through questionnaire_responses table
                            cursor.execute("""

                                SELECT ar.approval_id, ar.request_data 
                                FROM approval_requests ar
                                INNER JOIN questionnaire_responses qr ON qr.vendor_id = JSON_EXTRACT(ar.request_data, '$.request_data.vendor_id')
                                WHERE qr.assignment_id = %s
                                LIMIT 1

                            """, [str(assignment_id)])

                            result = cursor.fetchone()
                            
                            if not result:
                                print(f"❌ CRITICAL - All 3 methods failed. No approval found for assignment {assignment_id}.")
                            else:
                                print(f"✅ Found approval via questionnaire_responses join!")

                    

                    if result:

                        approval_id, request_data = result
                        
                        # CRITICAL: Store in outer scope for version creation
                        approval_id_for_version = approval_id

                        print(f"✓ Found approval_id: {approval_id} for assignment {assignment_id}")

                        

                        # Parse the existing request_data

                        if isinstance(request_data, str):

                            request_data_obj = json.loads(request_data)

                        else:

                            request_data_obj = request_data
                        
                        # CRITICAL: Store in outer scope for version creation
                        request_data_for_version = request_data_obj

                        

                        # FIFTH: Update the JSON request_data with values from database tables

                        if 'request_data' in request_data_obj:

                            rd = request_data_obj['request_data']

                            

                            # Update assignment_summary with overall score from database

                            if 'assignment_summary' in rd:

                                rd['assignment_summary']['overall_score'] = float(assignment.overall_score) if assignment.overall_score else None

                                print(f"Debug - Updated assignment_summary overall_score: {rd['assignment_summary']['overall_score']}")

                            

                            # Update questions_and_responses with scores from database

                            if 'questions_and_responses' in rd:

                                print(f"Debug - Updating {len(rd['questions_and_responses'])} questions with scores from database")

                                

                                # CRITICAL: Re-fetch responses to ensure we get the latest updated scores

                                latest_responses = QuestionnaireResponseSubmissions.objects.filter(

                                    assignment=assignment

                                ).select_related('question')

                                

                                # Create mapping of question_id to score/comment from database

                                db_scores = {}

                                for response in latest_responses:

                                    question_id_str = str(response.question.question_id)

                                    db_scores[question_id_str] = {

                                        'score': float(response.score) if response.score is not None else None,

                                        'comment': response.reviewer_comment or ''

                                    }

                                    print(f"Debug - DB Score for Q{question_id_str}: {response.score}")

                                

                                print(f"Debug - Final database scores mapping: {db_scores}")

                                

                                # Update each question with its score from database

                                for qr in rd['questions_and_responses']:

                                    question_id = str(qr.get('question_id'))

                                    

                                    if question_id in db_scores:

                                        qr['score'] = db_scores[question_id]['score']

                                        qr['reviewer_comment'] = db_scores[question_id]['comment']

                                        print(f"Debug - Updated JSON Q{question_id}: score={qr['score']}, comment={qr['reviewer_comment']}")

                                    else:

                                        print(f"Debug - No database score found for Q{question_id}")

                                        # CRITICAL FIX: Never leave score as null

                                        scoring_weight = qr.get('scoring_weight', 1.0)

                                        default_score = (float(scoring_weight) * 10) * 0.5

                                        qr['score'] = round(default_score, 2)

                                        qr['reviewer_comment'] = 'No score available in database'

                                        print(f"Debug - Set fallback score for JSON Q{question_id}: {qr['score']}")

                                

                                print(f"Debug - Final JSON questions updated with scores")

                                

                                # VERIFICATION: Double-check no null scores remain

                                null_scores = [q for q in rd['questions_and_responses'] if q.get('score') is None]

                                if null_scores:

                                    print(f"Warning - Found {len(null_scores)} questions with null scores after update!")

                                    for q in null_scores:

                                        scoring_weight = q.get('scoring_weight', 1.0)

                                        fallback_score = (float(scoring_weight) * 10) * 0.5

                                        q['score'] = round(fallback_score, 2)

                                        q['reviewer_comment'] = 'Fallback score applied'

                                        print(f"Debug - Applied emergency fallback score to Q{q.get('question_id')}: {q['score']}")

                                else:

                                    print("Debug - Verification passed: No null scores found in JSON")

                            

                            # Add final scoring summary to request_data

                            rd['final_scoring_summary'] = {

                                'overall_score': float(assignment.overall_score) if assignment.overall_score else None,

                                'final_decision': assignee_decision,

                                'assignee_comments': assignee_comments,

                                'scoring_completed_at': timezone.now().isoformat(),

                                'scored_by': assignee_id,

                                'question_scores': final_scores

                            }

                            

                            print(f"Debug - Final request_data structure updated")

                        

                        # Update the request_data in the database

                        cursor.execute("""

                            UPDATE approval_requests 

                            SET request_data = %s, updated_at = %s 

                            WHERE approval_id = %s

                        """, [json.dumps(request_data_obj), timezone.now(), approval_id])

                        

                        connection.commit()

                        

                        print(f"Updated approval request {approval_id} with final scoring data")

                        print(f"Overall score saved: {assignment.overall_score}")

                        print(f"Final decision: {assignee_decision}")

                        print(f"Questions updated with scores: {len(final_scores)}")
                    
                    # END of if result block - version creation will happen outside this block
                    
                    # CREATE VERSION ENTRY for assignee decision (MOVED OUTSIDE if result: block)
                    # This ensures version is created even if request_data update fails
                    if approval_id_for_version and assignee_decision in ['APPROVE', 'REJECT']:
                        print(f"\n{'='*80}")
                        print(f"🔄 CREATING VERSION for Assignee Decision: {assignee_decision}")
                        print(f"{'='*80}")
                        try:
                            # Determine version type based on decision
                            if assignee_decision == 'APPROVE':
                                version_type = 'FINAL'
                                version_label = f'Assignee Final Approval - Score: {assignment.overall_score:.1f}%'
                            else:  # REJECT
                                version_type = 'REVISION'
                                version_label = f'Assignee Rejection'
                            
                            # Create changes summary
                            changes_summary = f'Assignee made final decision: {assignee_decision}. '
                            changes_summary += f'Overall score: {assignment.overall_score:.2f}%. '
                            changes_summary += f'Updated {len(final_scores)} question scores.'
                            
                            # Get assignee details (use provided assignee_id or default)
                            assignee_name = f'Assignee {assignee_id}'
                            assignee_role = 'Final Assignee'
                            
                            # Try to get actual user name from database
                            try:
                                with connections['default'].cursor() as user_cursor:
                                    user_cursor.execute("""
                                        SELECT username FROM users_user WHERE id = %s
                                    """, [assignee_id])
                                    user_row = user_cursor.fetchone()
                                    if user_row:
                                        assignee_name = user_row[0]
                                        print(f"✓ Got assignee name from database: {assignee_name}")
                            except Exception as e:
                                print(f"⚠️  Could not fetch assignee name: {str(e)}")
                            
                            # Prepare change reason
                            change_reason = assignee_comments if assignee_comments else f'Final assignee decision: {assignee_decision}'
                            
                            print(f"📝 Version Details:")
                            print(f"   - Approval ID: {approval_id_for_version}")
                            print(f"   - Version Type: {version_type}")
                            print(f"   - Version Label: {version_label}")
                            print(f"   - Created By: {assignee_name} (ID: {assignee_id})")
                            print(f"   - Role: {assignee_role}")
                            print(f"   - Change Reason: {change_reason}")
                            
                            # Call create_approval_version helper function
                            print(f"🚀 Calling create_approval_version()...")
                            version_id = create_approval_version(
                                approval_id=approval_id_for_version,
                                version_type=version_type,
                                version_label=version_label,
                                json_payload=request_data_for_version if request_data_for_version else {},  # Use stored data or empty dict
                                changes_summary=changes_summary,
                                created_by=assignee_id,
                                created_by_name=assignee_name,
                                created_by_role=assignee_role,
                                change_reason=change_reason
                            )
                            
                            if version_id:
                                print(f"\n✅ SUCCESS! Version created: {version_id}")
                                print(f"✅ Assignee decision '{assignee_decision}' recorded in version table")
                                print(f"✅ Version number has been incremented for approval_id: {approval_id_for_version}")
                            else:
                                print(f"\n❌ FAILURE - create_approval_version returned None")
                                print(f"❌ Version was NOT created for assignee decision!")
                            
                            print(f"{'='*80}\n")
                                
                        except Exception as version_error:
                            print(f"\n❌❌❌ EXCEPTION creating version for assignee decision ❌❌❌")
                            print(f"Error: {str(version_error)}")
                            import traceback
                            traceback.print_exc()
                            print(f"❌ Version creation FAILED but operation will continue")
                            print(f"{'='*80}\n")
                            # Don't fail the entire operation if versioning fails
                    elif not approval_id_for_version and assignee_decision in ['APPROVE', 'REJECT']:
                        print(f"\n❌❌❌ CANNOT CREATE VERSION - approval_id not found for assignment {assignment_id} ❌❌❌")
                        print(f"❌ Assignee decision '{assignee_decision}' will NOT be recorded in version table!")
                        print(f"❌ This is a critical issue - check approval_requests table for this assignment")
                    else:
                        print(f"ℹ️  No version created - Decision is '{assignee_decision}' (only APPROVE/REJECT create versions)")

            except Exception as e:

                print(f"Error updating approval request with scoring data: {str(e)}")

                # Don't fail the entire operation if this update fails

        

        return Response({

            'success': True,

            'message': 'Final assignee scores and decision saved successfully',

            'assignment_id': assignment_id,

            'final_decision': assignee_decision,

            'overall_score': float(assignment.overall_score) if assignment.overall_score else None,

            'questions_updated': len(final_scores)

        }, status=status.HTTP_200_OK)

        

    except Exception as e:

        print(f"Error saving final assignee scores: {str(e)}")

        return Response({

            'error': 'Failed to save final scores',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('update_vendor')
@require_tenant
@tenant_filter
def update_question_scores_in_json(request):

    """Update individual question scores in the request_data JSON
    MULTI-TENANCY: Ensures assignment belongs to tenant's vendor
    """

    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)

        data = request.data

        assignment_id = data.get('assignment_id')

        question_scores = data.get('question_scores', [])  # List of {question_id, score, comment}

        

        if not assignment_id:

            return Response({

                'error': 'Assignment ID is required'

            }, status=status.HTTP_400_BAD_REQUEST)

        

        with connections['default'].cursor() as cursor:

            # Get the approval_id associated with this assignment

            cursor.execute("""

                SELECT ar.approval_id, ar.request_data 

                FROM approval_requests ar 

                WHERE JSON_EXTRACT(ar.request_data, '$.request_data.questionnaire_assignment_id') = %s

            """, [str(assignment_id)])

            

            result = cursor.fetchone()

            if not result:

                return Response({

                    'error': 'Approval request not found for this assignment'

                }, status=status.HTTP_404_NOT_FOUND)

            

            approval_id, request_data = result

            

            # Parse the existing request_data

            if isinstance(request_data, str):

                request_data_obj = json.loads(request_data)

            else:

                request_data_obj = request_data

            

            # Update questions_and_responses with AVERAGE scores from all reviewers

            if 'request_data' in request_data_obj:

                rd = request_data_obj['request_data']

                if 'questions_and_responses' in rd:

                    print(f"Debug - Calculating AVERAGE scores for {len(rd['questions_and_responses'])} questions")

                    

                    # Get all stages for this approval to calculate average scores

                    cursor.execute("""

                        SELECT stage_id, stage_name, assigned_user_name, response_data, stage_status

                        FROM approval_stages

                        WHERE approval_id = %s AND stage_status IN ('APPROVED', 'IN_PROGRESS')

                        ORDER BY stage_order

                    """, [approval_id])

                    

                    stages_data = cursor.fetchall()

                    print(f"Debug - Found {len(stages_data)} stages for average calculation")

                    

                    # Calculate average scores for each question

                    question_averages = {}

                    

                    for stage_row in stages_data:

                        stage_id, stage_name, user_name, response_data, stage_status = stage_row

                        

                        if response_data:

                            try:

                                if isinstance(response_data, str):

                                    stage_response = json.loads(response_data)

                                else:

                                    stage_response = response_data

                                

                                # Extract reviewer scores from this stage

                                reviewer_scores = stage_response.get('reviewer_scores', {})

                                print(f"Debug - Stage {stage_name} ({user_name}) reviewer_scores: {reviewer_scores}")

                                

                                # Process each question score from this reviewer

                                for question_id, score_data in reviewer_scores.items():

                                    question_id_str = str(question_id)

                                    score_value = score_data.get('score')

                                    

                                    if score_value is not None:

                                        if question_id_str not in question_averages:

                                            question_averages[question_id_str] = {

                                                'scores': [],

                                                'comments': [],

                                                'reviewers': []

                                            }

                                        

                                        question_averages[question_id_str]['scores'].append(float(score_value))

                                        question_averages[question_id_str]['comments'].append(score_data.get('comment', ''))

                                        question_averages[question_id_str]['reviewers'].append(user_name)

                                        

                            except Exception as e:

                                print(f"Debug - Error processing stage {stage_id}: {str(e)}")

                                continue

                    

                    print(f"Debug - Question averages calculated: {question_averages}")

                    

                    # Update each question with its AVERAGE score

                    updated_count = 0

                    for qr in rd['questions_and_responses']:

                        question_id = str(qr.get('question_id'))

                        

                        if question_id in question_averages:

                            scores_list = question_averages[question_id]['scores']

                            if scores_list:

                                # Calculate average score

                                average_score = sum(scores_list) / len(scores_list)

                                qr['score'] = round(average_score, 2)

                                

                                # Combine all reviewer comments

                                all_comments = [c for c in question_averages[question_id]['comments'] if c.strip()]

                                qr['reviewer_comment'] = '; '.join(all_comments) if all_comments else ''

                                

                                updated_count += 1

                                print(f"Debug - Updated Q{question_id}: average_score={qr['score']} (from {len(scores_list)} reviewers), comment={qr['reviewer_comment']}")

                            else:

                                print(f"Debug - No scores found for Q{question_id}")

                        else:

                            print(f"Debug - No average data for Q{question_id}")

                    

                    print(f"Debug - Updated {updated_count} questions with AVERAGE scores")

                

                # Update the request_data in the database

                cursor.execute("""

                    UPDATE approval_requests 

                    SET request_data = %s, updated_at = %s 

                    WHERE approval_id = %s

                """, [json.dumps(request_data_obj), timezone.now(), approval_id])

                

                connection.commit()

                

                return Response({

                    'success': True,

                    'message': 'Question scores updated successfully in JSON',

                    'approval_id': approval_id,

                    'questions_updated': updated_count

                }, status=status.HTTP_200_OK)

            else:

                return Response({

                    'error': 'Invalid request_data structure'

                }, status=status.HTTP_400_BAD_REQUEST)

                

    except Exception as e:

        print(f"Error updating question scores in JSON: {str(e)}")

        return Response({

            'error': 'Failed to update question scores',

            'details': str(e)

        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





def _end_response_approval_start_vendor_approval(vendor_id):
    """End Response Approval stage and start Vendor Approval stage"""
    try:
        from apps.vendor_core.models import LifecycleTracker, TempVendor
        from apps.vendor_core.views import get_lifecycle_stage_id_by_code
        from django.utils import timezone
        
        print(f"Debug - Starting lifecycle transition for vendor {vendor_id}: Response Approval -> Vendor Approval")
        current_time = timezone.now()
        
        # Get stage IDs - Response Approval (5) -> Vendor Approval (6)
        response_approval_stage_id = get_lifecycle_stage_id_by_code('RES_APP')
        vendor_approval_stage_id = get_lifecycle_stage_id_by_code('VEN_APP')
        
        print(f"Debug - Stage IDs: RES_APP={response_approval_stage_id}, VEN_APP={vendor_approval_stage_id}")
        
        if not response_approval_stage_id or not vendor_approval_stage_id:
            print(f"ERROR - Could not find stage IDs for vendor {vendor_id}")
            print(f"  RES_APP ID: {response_approval_stage_id}")
            print(f"  VEN_APP ID: {vendor_approval_stage_id}")
            return
        
        # End Response Approval stage
        response_approval_entry = LifecycleTracker.objects.filter(
            vendor_id=vendor_id,
            lifecycle_stage=response_approval_stage_id,
            ended_at__isnull=True
        ).first()
        
        if response_approval_entry:
            response_approval_entry.ended_at = current_time
            response_approval_entry.save()
            print(f"✓ Successfully ended Response Approval stage for vendor {vendor_id} at {current_time}")
        else:
            print(f"WARNING - No active Response Approval stage found for vendor {vendor_id}")
            # Check if there are any lifecycle entries for this vendor
            all_entries = LifecycleTracker.objects.filter(vendor_id=vendor_id)
            print(f"Debug - All lifecycle entries for vendor {vendor_id}: {list(all_entries.values('id', 'lifecycle_stage', 'started_at', 'ended_at'))}")
        
        # Start Vendor Approval stage
        new_entry = LifecycleTracker.objects.create(
            vendor_id=vendor_id,
            lifecycle_stage=vendor_approval_stage_id,
            started_at=current_time
        )
        print(f"✓ Successfully created Vendor Approval stage entry (ID: {new_entry.id}) for vendor {vendor_id}")
        
        # Update temp vendor current stage
        try:
            temp_vendor = TempVendor.objects.get(id=vendor_id)
            old_stage = temp_vendor.lifecycle_stage
            temp_vendor.lifecycle_stage = vendor_approval_stage_id
            temp_vendor.save()
            print(f"✓ Successfully updated temp vendor {vendor_id} lifecycle stage from {old_stage} to {vendor_approval_stage_id}")
        except TempVendor.DoesNotExist:
            print(f"ERROR - Temp vendor {vendor_id} not found")
        
        print(f"✓ COMPLETED - Successfully transitioned vendor {vendor_id} from Response Approval to Vendor Approval stage")
        
    except Exception as e:
        print(f"ERROR - Failed to transition from Response Approval to Vendor Approval for vendor {vendor_id}: {str(e)}")
        import traceback
        traceback.print_exc()





def _end_vendor_approval_stage(vendor_id):

    """End Vendor Approval stage (final completion)"""

    try:

        from apps.vendor_core.models import LifecycleTracker, TempVendor

        from apps.vendor_core.views import get_lifecycle_stage_id_by_code

        from django.utils import timezone

        

        current_time = timezone.now()

        

        # Get stage ID

        vendor_approval_stage_id = get_lifecycle_stage_id_by_code('VEN_APP')

        

        if not vendor_approval_stage_id:

            print(f"Warning: Could not find Vendor Approval stage ID for vendor {vendor_id}")

            return

        

        # End Vendor Approval stage

        vendor_approval_entry = LifecycleTracker.objects.filter(

            vendor_id=vendor_id,

            lifecycle_stage=vendor_approval_stage_id,

            ended_at__isnull=True

        ).first()

        

        if vendor_approval_entry:

            vendor_approval_entry.ended_at = current_time

            vendor_approval_entry.save()

            print(f"Ended Vendor Approval stage for vendor {vendor_id} - Lifecycle completed")

        

        # Update temp vendor status to completed

        temp_vendor = TempVendor.objects.get(id=vendor_id)

        temp_vendor.status = 'completed'

        temp_vendor.save()

        

        print(f"Vendor {vendor_id} lifecycle fully completed")

        

    except Exception as e:

        print(f"Error ending Vendor Approval stage for vendor {vendor_id}: {str(e)}")


def ensure_lifecycle_stage_exists(vendor_id, stage_code):
    """
    Ensure that a lifecycle stage exists for the given vendor and stage code
    Returns the stage_id if successful, None otherwise
    """
    try:
        from apps.vendor_core.models import LifecycleTracker, TempVendor
        from apps.vendor_core.views import get_lifecycle_stage_id_by_code
        from django.utils import timezone
        
        current_time = timezone.now()
        
        # Get stage ID
        stage_id = get_lifecycle_stage_id_by_code(stage_code)
        if not stage_id:
            print(f"ERROR - Could not find stage ID for code: {stage_code}")
            return None
        
        # Check if the stage already exists for this vendor
        existing_entry = LifecycleTracker.objects.filter(
            vendor_id=vendor_id,
            lifecycle_stage=stage_id
        ).first()
        
        if existing_entry:
            # If it exists but is ended, reactivate it
            if existing_entry.ended_at:
                existing_entry.ended_at = None
                existing_entry.started_at = current_time
                existing_entry.save()
                print(f"✓ Reactivated {stage_code} stage for vendor {vendor_id}")
        else:
            # End any currently active stages
            LifecycleTracker.objects.filter(
                vendor_id=vendor_id,
                ended_at__isnull=True
            ).update(ended_at=current_time)
            
            # Create new entry
            LifecycleTracker.objects.create(
                vendor_id=vendor_id,
                lifecycle_stage=stage_id,
                started_at=current_time
            )
            print(f"✓ Started {stage_code} stage for vendor {vendor_id}")
        
        # Update temp vendor lifecycle stage
        TempVendor.objects.filter(id=vendor_id).update(
            lifecycle_stage=stage_id,
            updated_at=current_time
        )
        
        return stage_id
        
    except Exception as e:
        print(f"ERROR - Failed to ensure lifecycle stage {stage_code} for vendor {vendor_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def _end_questionnaire_approval_start_questionnaire_response(vendor_id):
    """End Questionnaire Approval stage and start Questionnaire Response stage"""
    try:
        from apps.vendor_core.models import LifecycleTracker, TempVendor
        from apps.vendor_core.views import get_lifecycle_stage_id_by_code
        from django.utils import timezone
        
        print(f"Debug - Starting lifecycle transition for vendor {vendor_id}: Questionnaire Approval -> Questionnaire Response")
        current_time = timezone.now()
        
        # Get stage IDs - Questionnaire Approval (3) -> Questionnaire Response (4)
        questionnaire_approval_stage_id = get_lifecycle_stage_id_by_code('QUES_APP')
        questionnaire_response_stage_id = get_lifecycle_stage_id_by_code('QUES_RES')
        
        print(f"Debug - Stage IDs: QUES_APP={questionnaire_approval_stage_id}, QUES_RES={questionnaire_response_stage_id}")
        
        if not questionnaire_approval_stage_id or not questionnaire_response_stage_id:
            print(f"ERROR - Could not find stage IDs for vendor {vendor_id}")
            print(f"  QUES_APP ID: {questionnaire_approval_stage_id}")
            print(f"  QUES_RES ID: {questionnaire_response_stage_id}")
            return
        
        # First, make sure the Questionnaire Approval stage exists before ending it
        # This is a safety check in case the stage was never properly created
        questionnaire_approval_entry = LifecycleTracker.objects.filter(
            vendor_id=vendor_id,
            lifecycle_stage=questionnaire_approval_stage_id
        ).first()
        
        if not questionnaire_approval_entry:
            # Create it with both start and end time
            print(f"WARNING - No Questionnaire Approval entry found for vendor {vendor_id}, creating one with immediate completion")
            LifecycleTracker.objects.create(
                vendor_id=vendor_id,
                lifecycle_stage=questionnaire_approval_stage_id,
                started_at=current_time,
                ended_at=current_time
            )
        elif questionnaire_approval_entry.ended_at is None:
            # Normal case: end the active stage
            questionnaire_approval_entry.ended_at = current_time
            questionnaire_approval_entry.save()
            print(f"✓ Ended Questionnaire Approval stage for vendor {vendor_id}")
        else:
            print(f"INFO - Questionnaire Approval stage for vendor {vendor_id} was already ended")
        
        # Start Questionnaire Response stage
        questionnaire_response_entry = LifecycleTracker.objects.filter(
            vendor_id=vendor_id,
            lifecycle_stage=questionnaire_response_stage_id
        ).first()
        
        if not questionnaire_response_entry:
            # Create new entry for Questionnaire Response stage
            LifecycleTracker.objects.create(
                vendor_id=vendor_id,
                lifecycle_stage=questionnaire_response_stage_id,
                started_at=current_time
            )
            print(f"✓ Started Questionnaire Response stage for vendor {vendor_id}")
        else:
            # Update existing entry if needed
            if questionnaire_response_entry.ended_at is not None:
                questionnaire_response_entry.started_at = current_time
                questionnaire_response_entry.ended_at = None
                questionnaire_response_entry.save()
                print(f"✓ Reactivated Questionnaire Response stage for vendor {vendor_id}")
            else:
                print(f"✓ Questionnaire Response stage already active for vendor {vendor_id}")
        
        # Update temp vendor lifecycle stage
        try:
            temp_vendor = TempVendor.objects.get(id=vendor_id)
            temp_vendor.lifecycle_stage = questionnaire_response_stage_id
            temp_vendor.save()
            print(f"✓ Updated temp vendor lifecycle stage to Questionnaire Response for vendor {vendor_id}")
        except TempVendor.DoesNotExist:
            print(f"WARNING - TempVendor with ID {vendor_id} not found")
        
    except Exception as e:
        print(f"Error transitioning from Questionnaire Approval to Questionnaire Response for vendor {vendor_id}: {str(e)}")
        import traceback
        traceback.print_exc()




@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def test_lifecycle_stage_3(request, vendor_id):
    """Test function to ensure lifecycle stage 3 is correctly recorded for a vendor
    MULTI-TENANCY: Ensures vendor belongs to tenant
    """
    try:
        # Convert vendor_id to integer
        vendor_id = int(vendor_id)
        
        # Use our helper function to ensure lifecycle stage 3 exists
        lifecycle_stage_id = ensure_lifecycle_stage_exists(vendor_id, 'QUES_APP')
        
        if lifecycle_stage_id:
            # Check if the stage was created successfully
            from apps.vendor_core.models import LifecycleTracker
            stage_entry = LifecycleTracker.objects.filter(
                vendor_id=vendor_id,
                lifecycle_stage=lifecycle_stage_id,
                ended_at__isnull=True
            ).first()
            
            if stage_entry:
                return Response({
                    'success': True,
                    'message': f'Lifecycle Stage 3 (Questionnaire Approval) successfully created for vendor {vendor_id}',
                    'stage_id': stage_id,
                    'started_at': stage_entry.started_at
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': f'Lifecycle Stage 3 entry not found for vendor {vendor_id} after creation attempt'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                'success': False,
                'message': f'Failed to create Lifecycle Stage 3 for vendor {vendor_id}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error testing lifecycle stage 3: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def check_risk_generation_status(request, approval_id):
    """Check the status of risk generation for a given approval ID
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    try:
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return Response({'error': 'Tenant context not found'}, status=403)
        
        # Use tprm database connection for queries
        from django.db import connections as db_connections
        if 'tprm' in db_connections.databases:
            db_connection = db_connections['tprm']
        else:
            db_connection = db_connections['default']
        
        # First, check if the approval exists and get vendor_id from request_data
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT overall_status, request_data 
                FROM approval_requests 
                WHERE approval_id = %s
            """, [approval_id])
            
            result = cursor.fetchone()
            
            if not result:
                return Response({
                    'status': 'not_found',
                    'message': 'Approval request not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            overall_status, request_data = result
            
            # Parse request_data to get vendor_id
            vendor_id = None
            if request_data:
                try:
                    if isinstance(request_data, str):
                        request_data_obj = json.loads(request_data)
                    else:
                        request_data_obj = request_data
                    
                    rd = request_data_obj.get('request_data', request_data_obj)
                    vendor_data = rd.get('vendor_data', {})
                    vendor_id = vendor_data.get('vendor_id') or vendor_data.get('id')
                except:
                    pass
            
            # Check if risks have been generated for this vendor
            # Risks are stored with entity='vendor_management' and row=vendor_id
            # MULTI-TENANCY: Filter by tenant by joining with temp_vendor
            if vendor_id:
                cursor.execute("""
                    SELECT COUNT(*) as risk_count
                    FROM risk_tprm r
                    LEFT JOIN temp_vendor tv ON r.`row` = CAST(tv.id AS CHAR)
                    WHERE r.entity = 'vendor_management'
                    AND r.`row` = %s
                    AND (tv.TenantId = %s OR tv.TenantId IS NULL)
                """, [str(vendor_id), tenant_id])
                
                risk_result = cursor.fetchone()
                risk_count = risk_result[0] if risk_result else 0
                
                if risk_count > 0:
                    return Response({
                        'status': 'completed',
                        'risk_count': risk_count,
                        'message': f'Risk generation completed. {risk_count} risks identified.'
                    }, status=status.HTTP_200_OK)
            
            # If no risks found but approval is approved, risk generation might be in progress
            if overall_status == 'APPROVED':
                return Response({
                    'status': 'in_progress',
                    'risk_count': 0,
                    'message': 'Risk generation is in progress...'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'pending',
                    'message': 'Approval not yet completed'
                }, status=status.HTTP_200_OK)
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error checking risk generation status: {str(e)}")
        print(f"Traceback: {error_trace}")
        return Response({
            'error': 'Failed to check risk generation status',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('view_vendors')
@require_tenant
@tenant_filter
def get_approval_version_history(request, approval_id):
    """
    Get complete version history for an approval request with properly incremented version numbers.
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    
    Returns all versions ordered by version_number, showing every decision made in the approval workflow.
    Each approval, rejection, and decision is recorded with an incremented version number.
    """
    try:
        with connections['default'].cursor() as cursor:
            # First, verify the approval exists
            cursor.execute("""
                SELECT ar.approval_id, ar.request_title, ar.overall_status, aw.workflow_type, ar.created_at
                FROM approval_requests ar
                JOIN approval_workflows aw ON ar.workflow_id = aw.workflow_id
                WHERE ar.approval_id = %s
            """, [approval_id])
            
            approval_row = cursor.fetchone()
            if not approval_row:
                return Response({
                    'error': 'Approval request not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            approval_id, request_title, overall_status, workflow_type, created_at = approval_row
            
            # Get all versions for this approval, ordered by version number
            cursor.execute("""
                SELECT 
                    version_id,
                    version_number,
                    version_label,
                    version_type,
                    changes_summary,
                    created_by,
                    created_by_name,
                    created_by_role,
                    change_reason,
                    is_current,
                    is_approved,
                    parent_version_id,
                    created_at
                FROM approval_request_versions
                WHERE approval_id = %s
                ORDER BY version_number ASC
            """, [approval_id])
            
            version_rows = cursor.fetchall()
            
            # Build version history
            versions = []
            for row in version_rows:
                (version_id, version_number, version_label, version_type, changes_summary,
                 created_by, created_by_name, created_by_role, change_reason,
                 is_current, is_approved, parent_version_id, version_created_at) = row
                
                versions.append({
                    'version_id': version_id,
                    'version_number': version_number,
                    'version_label': version_label,
                    'version_type': version_type,
                    'changes_summary': changes_summary,
                    'created_by': created_by,
                    'created_by_name': created_by_name,
                    'created_by_role': created_by_role,
                    'change_reason': change_reason,
                    'is_current': bool(is_current),
                    'is_approved': bool(is_approved),
                    'parent_version_id': parent_version_id,
                    'created_at': version_created_at.isoformat() if version_created_at else None
                })
            
            # Get current version number (highest version number)
            current_version_number = max([v['version_number'] for v in versions]) if versions else 0
            
            return Response({
                'approval_id': approval_id,
                'request_title': request_title,
                'overall_status': overall_status,
                'workflow_type': workflow_type,
                'approval_created_at': created_at.isoformat() if created_at else None,
                'current_version_number': current_version_number,
                'total_versions': len(versions),
                'versions': versions
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        print(f"Error retrieving version history for approval {approval_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': 'Failed to retrieve version history',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


