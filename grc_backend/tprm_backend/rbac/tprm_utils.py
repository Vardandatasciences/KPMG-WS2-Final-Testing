"""
Enhanced RBAC Utilities for TPRM System

This module provides comprehensive utilities for checking permissions using the rbac_tprm table schema.
Supports all TPRM modules: RFP, Contract, Vendor, Risk, Compliance, and BCP/DRP.
"""

import logging
from django.utils import timezone
from .models import RBACTPRM
from django.db import models

logger = logging.getLogger(__name__)

class RBACTPRMUtils:
    """
    Enhanced RBAC Utility class for permission checking using the rbac_tprm table schema
    """
    
    @staticmethod
    def get_user_id_from_request(request):
        """
        Get user_id from JWT token in Authorization header or session
        Supports both JWT and session authentication
        """
        logger.debug("[RBAC TPRM] Starting get_user_id_from_request")
        
        # Try to get user_id from request.user (set by JWTAuthentication)
        try:
            if hasattr(request, 'user') and request.user and not request.user.is_anonymous:
                # Check for UserId (custom Users model field)
                if hasattr(request.user, 'UserId'):
                    user_id = request.user.UserId
                    if user_id:
                        logger.info(f"[RBAC TPRM] Successfully extracted user_id from request.user.UserId: {user_id}")
                        return user_id
                # Check for userid (lowercase)
                if hasattr(request.user, 'userid'):
                    user_id = request.user.userid
                    if user_id:
                        logger.info(f"[RBAC TPRM] Successfully extracted user_id from request.user.userid: {user_id}")
                        return user_id
                # Check for id (Django default) - but only if it's not None
                if hasattr(request.user, 'id'):
                    user_id = request.user.id
                    if user_id:  # Only return if not None
                        logger.info(f"[RBAC TPRM] Successfully extracted user_id from request.user.id: {user_id}")
                        return user_id
        except Exception as e:
            logger.error(f"[RBAC TPRM] Error extracting user_id from request.user: {e}")
        
        # Try JWT authentication directly
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
                # Decode JWT token directly
                import jwt
                from django.conf import settings
                secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                
                # Try multiple field names for user_id in JWT payload
                user_id = payload.get('user_id') or payload.get('UserId') or payload.get('id')
                
                if user_id:
                    logger.info(f"[RBAC TPRM] Successfully extracted user_id from JWT: {user_id}")
                    return user_id
                else:
                    logger.warning(f"[RBAC TPRM] No user_id found in JWT payload. Available keys: {list(payload.keys())}")
                    
        except Exception as e:
            logger.error(f"[RBAC TPRM] Error extracting user_id from JWT: {e}")
        
        # Fallback to session authentication
        try:
            user_id = request.session.get('user_id') or request.session.get('grc_user_id')
            if user_id:
                logger.info(f"[RBAC TPRM] Successfully extracted user_id from session: {user_id}")
                return user_id
            else:
                logger.warning("[RBAC TPRM] No user_id found in session")
                
        except Exception as e:
            logger.error(f"[RBAC TPRM] Error extracting user_id from session: {e}")
        
        logger.warning("[RBAC TPRM] No user_id found in JWT token or session")
        return None
    
    @staticmethod
    def get_user_rbac_record(user_id, force_refresh=False):
        """Get the RBAC TPRM record for a user with extensive debugging
        
        Args:
            user_id: The user ID to look up
            force_refresh: If True, bypasses any cache and forces a fresh database query
        """
        try:
            logger.debug(f"[RBAC TPRM] Looking up RBAC record for user_id: {user_id}, force_refresh: {force_refresh}")
            
            # If force_refresh, clear any potential cache first
            if force_refresh:
                try:
                    from django.core.cache import cache
                    cache_key = f"rbac_tprm_user_{user_id}"
                    cache.delete(cache_key)
                    logger.debug(f"[RBAC TPRM] Cleared cache for user {user_id}")
                except Exception as cache_error:
                    logger.debug(f"[RBAC TPRM] Cache clear note: {cache_error}")
            
            # If force_refresh, use raw SQL to bypass ORM query cache completely
            if force_refresh:
                try:
                    from django.db import connections
                    tprm_connection = connections['tprm'] if 'tprm' in connections.databases else connections['default']
                    
                    # Use raw SQL to get fresh data, bypassing ORM cache
                    with tprm_connection.cursor() as raw_cursor:
                        raw_cursor.execute("""
                            SELECT RBACId, UserId, UserName, Role, IsActive,
                                   ViewVendors, CreateVendor, UpdateVendor, DeleteVendor,
                                   ViewRFP, CreateRFP, EditRFP, DeleteRFP, CloneRFP,
                                   SubmitRFPForReview, ApproveRFP, RejectRFP, AssignRFPReviewers,
                                   ViewRFPApprovalStatus
                            FROM `rbac_tprm`
                            WHERE UserId = %s AND IsActive = 'Y'
                            LIMIT 1
                        """, [user_id])
                        raw_row = raw_cursor.fetchone()
                        
                        if raw_row:
                            # Create a temporary RBACTPRM instance with fresh data
                            # This bypasses ORM query cache
                            rbac_record = RBACTPRM()
                            rbac_record.rbac_id = raw_row[0]
                            rbac_record.user_id = raw_row[1]
                            rbac_record.username = raw_row[2]
                            rbac_record.role = raw_row[3]
                            rbac_record.is_active = raw_row[4]
                            # Set permission fields directly from database
                            if len(raw_row) > 5:
                                # Vendor permissions
                                rbac_record.view_vendors = bool(raw_row[5]) if raw_row[5] is not None else False
                                rbac_record.create_vendor = bool(raw_row[6]) if len(raw_row) > 6 and raw_row[6] is not None else False
                                rbac_record.update_vendor = bool(raw_row[7]) if len(raw_row) > 7 and raw_row[7] is not None else False
                                rbac_record.delete_vendor = bool(raw_row[8]) if len(raw_row) > 8 and raw_row[8] is not None else False
                                # RFP permissions
                                rbac_record.view_rfp = bool(raw_row[9]) if len(raw_row) > 9 and raw_row[9] is not None else False
                                rbac_record.create_rfp = bool(raw_row[10]) if len(raw_row) > 10 and raw_row[10] is not None else False
                                rbac_record.edit_rfp = bool(raw_row[11]) if len(raw_row) > 11 and raw_row[11] is not None else False
                                rbac_record.delete_rfp = bool(raw_row[12]) if len(raw_row) > 12 and raw_row[12] is not None else False
                                rbac_record.clone_rfp = bool(raw_row[13]) if len(raw_row) > 13 and raw_row[13] is not None else False
                                rbac_record.submit_rfp_for_review = bool(raw_row[14]) if len(raw_row) > 14 and raw_row[14] is not None else False
                                rbac_record.approve_rfp = bool(raw_row[15]) if len(raw_row) > 15 and raw_row[15] is not None else False
                                rbac_record.reject_rfp = bool(raw_row[16]) if len(raw_row) > 16 and raw_row[16] is not None else False
                                rbac_record.assign_rfp_reviewers = bool(raw_row[17]) if len(raw_row) > 17 and raw_row[17] is not None else False
                                rbac_record.view_rfp_approval_status = bool(raw_row[18]) if len(raw_row) > 18 and raw_row[18] is not None else False
                            
                            logger.debug(f"[RBAC TPRM] Retrieved fresh RBAC data via raw SQL for user {user_id}")
                            
                            if not rbac_record:
                                logger.warning(f"[RBAC TPRM] No active RBAC record found for user {user_id}")
                                return None
                            
                            logger.info(f"[RBAC TPRM] Found active RBAC record for user {user_id}: role={rbac_record.role}")
                            return rbac_record
                        else:
                            logger.warning(f"[RBAC TPRM] No active RBAC record found for user {user_id} (raw SQL)")
                            return None
                except Exception as raw_error:
                    logger.warning(f"[RBAC TPRM] Raw SQL query failed, falling back to ORM: {raw_error}")
                    # Fall through to ORM query
            
            # Standard ORM query (may use cached data)
            rbac_record = RBACTPRM.objects.filter(user_id=user_id, is_active='Y').first()
            
            if not rbac_record:
                logger.warning(f"[RBAC TPRM] No active RBAC record found for user {user_id}")
                # Try to find any record for debugging
                all_records = RBACTPRM.objects.filter(user_id=user_id)
                if all_records.exists():
                    logger.debug(f"[RBAC TPRM] Found {all_records.count()} inactive records for user {user_id}")
                else:
                    logger.debug(f"[RBAC TPRM] No RBAC records at all for user {user_id}")
                return None
            
            logger.info(f"[RBAC TPRM] Found active RBAC record for user {user_id}: role={rbac_record.role}")
            logger.debug(f"[RBAC TPRM] User details - username: {rbac_record.username}, role: {rbac_record.role}")
            
            return rbac_record
            
        except Exception as e:
            logger.error(f"[RBAC TPRM] Error getting RBAC record for user {user_id}: {e}")
            return None
    
    @staticmethod
    def check_permission(user_id, permission_name, force_refresh=False):
        """
        Check if user has a specific permission
        
        Args:
            user_id: User ID to check
            permission_name: Name of the permission field to check (can be either db_column name or model field name)
            force_refresh: If True, forces a fresh database query bypassing any cache
        
        Returns:
            bool: True if user has permission, False otherwise
        """
        try:
            # If force_refresh, use raw SQL to completely bypass ORM cache
            if force_refresh:
                try:
                    from django.db import connections
                    tprm_connection = connections['tprm'] if 'tprm' in connections.databases else connections['default']
                    
                    # Convert permission name to database column name
                    # First try to get from model field mapping
                    db_column = None
                    try:
                        # Check if permission_name is a model field, get its db_column
                        if hasattr(RBACTPRM, permission_name):
                            field = RBACTPRM._meta.get_field(permission_name)
                            db_column = field.db_column
                    except Exception:
                        pass
                    
                    # If not found, try converting from PascalCase to snake_case and back
                    if not db_column:
                        model_field = RBACTPRMUtils.get_model_field_name_from_db_column(permission_name)
                        if model_field and hasattr(RBACTPRM, model_field):
                            try:
                                field = RBACTPRM._meta.get_field(model_field)
                                db_column = field.db_column
                            except Exception:
                                pass
                    
                    # If still not found, assume permission_name is already a db_column (PascalCase)
                    if not db_column:
                        # Convert snake_case to PascalCase
                        db_column = ''.join(word.capitalize() for word in permission_name.split('_'))
                    
                    # Use raw SQL to check permission directly
                    with tprm_connection.cursor() as raw_cursor:
                        raw_cursor.execute(f"""
                            SELECT `{db_column}` FROM `rbac_tprm`
                            WHERE UserId = %s AND IsActive = 'Y'
                            LIMIT 1
                        """, [user_id])
                        raw_row = raw_cursor.fetchone()
                        
                        if raw_row and raw_row[0] == 1:
                            logger.debug(f"[RBAC TPRM] Permission {permission_name} ({db_column}) for user {user_id}: True (raw SQL)")
                            return True
                        else:
                            logger.debug(f"[RBAC TPRM] Permission {permission_name} ({db_column}) for user {user_id}: False (raw SQL)")
                            return False
                except Exception as raw_error:
                    logger.warning(f"[RBAC TPRM] Raw SQL permission check failed, falling back to ORM: {raw_error}")
                    # Fall through to ORM query
            
            # Standard ORM-based permission check
            rbac_record = RBACTPRMUtils.get_user_rbac_record(user_id, force_refresh=force_refresh)
            if not rbac_record:
                logger.warning(f"[RBAC TPRM] No RBAC record found for user {user_id}")
                return False
            
            # First check if permission_name is already a valid model field name
            if hasattr(rbac_record, permission_name):
                has_permission = getattr(rbac_record, permission_name)
                logger.debug(f"[RBAC TPRM] Permission {permission_name} for user {user_id}: {has_permission}")
                return bool(has_permission)
            
            # If not found as model field, try converting from PascalCase to snake_case
            model_field_name = RBACTPRMUtils.get_model_field_name_from_db_column(permission_name)
            logger.debug(f"[RBAC TPRM] Converting permission '{permission_name}' to model field '{model_field_name}'")
            
            # Check if the permission field exists and is True
            if hasattr(rbac_record, model_field_name):
                has_permission = getattr(rbac_record, model_field_name)
                logger.debug(f"[RBAC TPRM] Permission {model_field_name} for user {user_id}: {has_permission}")
                return bool(has_permission)
            else:
                logger.warning(f"[RBAC TPRM] Permission field {model_field_name} not found in RBAC model")
                return False
                
        except Exception as e:
            logger.error(f"[RBAC TPRM] Error checking permission {permission_name} for user {user_id}: {e}")
            return False
    
    @staticmethod
    def check_rfp_permission(user_id, permission_type):
        """Check RFP-related permissions"""
        # Handle both simplified types and full database column names
        rfp_permissions = {
            # Simplified types
            'create': 'create_rfp',
            'edit': 'edit_rfp',
            'view': 'view_rfp',
            'delete': 'delete_rfp',
            'clone': 'clone_rfp',
            'submit': 'submit_rfp_for_review',
            'approve': 'approve_rfp',
            'reject': 'reject_rfp',
            'assign_reviewers': 'assign_rfp_reviewers',
            'view_approval_status': 'view_rfp_approval_status',
            'view_versions': 'view_rfp_versions',
            'create_version': 'create_rfp_version',
            'edit_version': 'edit_rfp_version',
            'view_version': 'view_rfp_version',
            'evaluate': 'score_rfp_response',  # Map to actual DB field
            'assign_evaluators': 'assign_rfp_evaluators',
            
            # Full database column names (PascalCase)
            'CreateRFP': 'create_rfp',
            'EditRFP': 'edit_rfp',
            'ViewRFP': 'view_rfp',
            'DeleteRFP': 'delete_rfp',
            'CloneRFP': 'clone_rfp',
            'SubmitRFPForReview': 'submit_rfp_for_review',
            'ApproveRFP': 'approve_rfp',
            'RejectRFP': 'reject_rfp',
            'AssignRFPReviewers': 'assign_rfp_reviewers',
            'ViewRFPApprovalStatus': 'view_rfp_approval_status',
            'ViewRFPVersions': 'view_rfp_versions',
            'CreateRFPVersion': 'create_rfp_version',
            'EditRFPVersion': 'edit_rfp_version',
            'ViewRFPVersion': 'view_rfp_version',
            'EvaluateRFP': 'score_rfp_response',  # Map to actual DB field
            'AssignRFPEvaluators': 'assign_rfp_evaluators',
            
            # Direct field names (snake_case) - passthrough
            'create_rfp': 'create_rfp',
            'edit_rfp': 'edit_rfp',
            'view_rfp': 'view_rfp',
            'delete_rfp': 'delete_rfp',
            'clone_rfp': 'clone_rfp',
            'submit_rfp_for_review': 'submit_rfp_for_review',
            'approve_rfp': 'approve_rfp',
            'reject_rfp': 'reject_rfp',
            'assign_rfp_reviewers': 'assign_rfp_reviewers',
            'view_rfp_approval_status': 'view_rfp_approval_status',
            'view_rfp_versions': 'view_rfp_versions',
            'create_rfp_version': 'create_rfp_version',
            'edit_rfp_version': 'edit_rfp_version',
            'view_rfp_version': 'view_rfp_version',
            'evaluate_rfp': 'score_rfp_response',  # Map to actual DB field that exists
            'assign_rfp_evaluators': 'assign_rfp_evaluators',
            'create_rfp_response': 'submit_rfp_response',  # Map to actual DB field (no 'create', use 'submit')
            'submit_rfp_response': 'submit_rfp_response',
            'view_rfp_responses': 'view_rfp_responses',
            'score_rfp_response': 'score_rfp_response',
            'withdraw_rfp_response': 'withdraw_rfp_response',
            'view_rfp_response_scores': 'view_rfp_response_scores',
        }
        
        permission_field = rfp_permissions.get(permission_type)
        if permission_field:
            return RBACTPRMUtils.check_permission(user_id, permission_field)
        else:
            logger.warning(f"[RBAC TPRM] Unknown RFP permission type: {permission_type}")
            return False
    
    @staticmethod
    def check_contract_permission(user_id, permission_type):
        """Check contract-related permissions"""
        # Handle both simplified types and full database column names
        contract_permissions = {
            # Simplified types
            'list': 'list_contracts',
            'create': 'create_contract',
            'update': 'update_contract',
            'delete': 'delete_contract',
            'approve': 'approve_contract',
            'reject': 'reject_contract',
            'create_term': 'create_contract_term',
            'list_terms': 'list_contract_terms',
            'update_term': 'update_contract_term',
            'delete_term': 'delete_contract_term',
            'list_renewals': 'list_contract_renewals',
            'create_renewal': 'create_contract_renewal',
            'approve_renewal': 'approve_contract_renewal',
            'reject_renewal': 'reject_contract_renewal',
            
            # Full database column names
            'ListContracts': 'list_contracts',
            'CreateContract': 'create_contract',
            'UpdateContract': 'update_contract',
            'DeleteContract': 'delete_contract',
            'ApproveContract': 'approve_contract',
            'RejectContract': 'reject_contract',
            'CreateContractTerm': 'create_contract_term',
            'ListContractTerms': 'list_contract_terms',
            'UpdateContractTerm': 'update_contract_term',
            'DeleteContractTerm': 'delete_contract_term',
            'ListContractRenewals': 'list_contract_renewals',
            'CreateContractRenewal': 'create_contract_renewal',
            'ApproveContractRenewal': 'approve_contract_renewal',
            'RejectContractRenewal': 'reject_contract_renewal',
            
            # Contract Analysis & Dashboard Permissions
            'ContractDashboard': 'contract_dashboard',
            'ContractSearch': 'contract_search',
            'TriggerOCR': 'trigger_ocr',
            'GetNLPClauses': 'get_nlp_clauses',
            'CreateContractAudit': 'create_contract_audit',
            'PerformContractAudit': 'perform_contract_audit',
            'GetContractHistory': 'get_contract_history',
            'CompareContractVersion': 'compare_contract_version',
            'DownloadContractDocument': 'download_contract_document',
            'ValidateContractData': 'validate_contract_data',
            
            # Simplified versions for Contract Analysis permissions
            'perform_audit': 'perform_contract_audit',
            'perform_contract_audit': 'perform_contract_audit'
        }
        
        permission_field = contract_permissions.get(permission_type)
        if permission_field:
            return RBACTPRMUtils.check_permission(user_id, permission_field)
        else:
            logger.warning(f"[RBAC TPRM] Unknown contract permission type: {permission_type}")
            return False
    
    @staticmethod
    def check_vendor_permission(user_id, permission_type, force_refresh=False):
        """Check vendor-related permissions
        
        Args:
            user_id: User ID to check
            permission_type: Type of vendor permission ('view', 'create', 'update', 'delete', etc.)
            force_refresh: If True, forces a fresh database query bypassing any cache
        """
        # Handle both simplified types and full database column names
        vendor_permissions = {
            # Simplified types for backward compatibility
            'view': 'view_vendors',
            'create': 'create_vendor',
            'update': 'update_vendor',
            'delete': 'delete_vendor',
            'submit_approval': 'submit_vendor_for_approval',
            'approve_reject': 'approve_reject_vendor',
            'submit_for_approval': 'submit_vendor_for_approval',
            
            # Full model field names (snake_case)
            'view_vendors': 'view_vendors',
            'create_vendor': 'create_vendor',
            'update_vendor': 'update_vendor',
            'delete_vendor': 'delete_vendor',
            'submit_vendor_for_approval': 'submit_vendor_for_approval',
            'approve_reject_vendor': 'approve_reject_vendor',
            
            # Vendor lifecycle permissions
            'view_risk_profile': 'view_risk_profile',
            'view_lifecycle_history': 'view_lifecycle_history',
            
            # Questionnaire permissions
            'assign_questionnaires': 'assign_questionnaires',
            'submit_questionnaire_responses': 'submit_questionnaire_responses',
            'review_approve_responses': 'review_approve_responses',
            
            # Risk assessment permissions
            'view_risk_assessments': 'view_risk_assessments',
            'create_risk_assessments': 'create_risk_assessments',
            'assess_vendor_risk': 'assess_vendor_risk',
            'view_vendor_risk_scores': 'view_vendor_risk_scores',
            
            # Screening permissions
            'initiate_screening': 'initiate_screening',
            'resolve_screening_matches': 'resolve_screening_matches',
            'view_screening_results': 'view_screening_results',
            
            # Full database column names (PascalCase)
            'ViewVendors': 'view_vendors',
            'CreateVendor': 'create_vendor',
            'UpdateVendor': 'update_vendor',
            'DeleteVendor': 'delete_vendor',
            'SubmitVendorForApproval': 'submit_vendor_for_approval',
            'ApproveRejectVendor': 'approve_reject_vendor',
            'ViewRiskProfile': 'view_risk_profile',
            'ViewLifecycleHistory': 'view_lifecycle_history',
            'AssignQuestionnaires': 'assign_questionnaires',
            'SubmitQuestionnaireResponses': 'submit_questionnaire_responses',
            'ReviewApproveResponses': 'review_approve_responses',
            'ViewRiskAssessments': 'view_risk_assessments',
            'InitiateScreening': 'initiate_screening',
            'ResolveScreeningMatches': 'resolve_screening_matches',
            'ViewScreeningResults': 'view_screening_results'
        }
        
        permission_field = vendor_permissions.get(permission_type)
        if permission_field:
            return RBACTPRMUtils.check_permission(user_id, permission_field, force_refresh=force_refresh)
        else:
            logger.warning(f"[RBAC TPRM] Unknown vendor permission type: {permission_type}")
            return False
    
    @staticmethod
    def check_risk_permission(user_id, permission_type):
        """Check risk-related permissions"""
        risk_permissions = {
            'assess_vendor': 'assess_vendor_risk',
            'view_vendor_scores': 'view_vendor_risk_scores',
            'identify_in_plans': 'identify_risks_in_plans',
            'view_identified': 'view_identified_risks',
            'manage_mitigation': 'manage_risk_mitigation_plans',
            'view_mitigation_status': 'view_risk_mitigation_status',
            'view_profile': 'view_risk_profile',
            'view_assessments': 'view_risk_assessments',
            'create_assessments': 'create_risk_assessments',
            'recalculate_scores': 'recalculate_risk_scores'
        }
        
        permission_field = risk_permissions.get(permission_type)
        if permission_field:
            return RBACTPRMUtils.check_permission(user_id, permission_field)
    
    @staticmethod
    def check_sla_permission(user_id, permission_type):
        """Check SLA-related permissions"""
        # Handle both simplified types and full database column names
        sla_permissions = {
            # Simplified types
            'view': 'view_sla',
            'create': 'create_sla',
            'update': 'update_sla',
            'delete': 'delete_sla',
            'activate_deactivate': 'activate_deactivate_sla',
            
            # Full database column names
            'ViewSLA': 'view_sla',
            'CreateSLA': 'create_sla',
            'UpdateSLA': 'update_sla',
            'DeleteSLA': 'delete_sla',
            'ActivateDeactivateSLA': 'activate_deactivate_sla'
        }
        
        permission_field = sla_permissions.get(permission_type)
        if permission_field:
            return RBACTPRMUtils.check_permission(user_id, permission_field)
        else:
            logger.warning(f"[RBAC TPRM] Unknown SLA permission type: {permission_type}")
            return False
    
    @staticmethod
    def check_compliance_permission(user_id, permission_type):
        """Check compliance-related permissions"""
        compliance_permissions = {
            'generate_audit_reports': 'generate_compliance_audit_reports',
            'review_regulatory': 'review_regulatory_compliance',
            'audit_against_regulations': 'audit_compliance_against_regulations',
            'generate_legal_reports': 'generate_legal_compliance_reports',
            'view_compliance_status': 'view_compliance_status_of_plans',
            'audit_documents': 'audit_compliance_of_documents',
            'configure_security': 'configure_document_security_settings',
            'view_access_logs': 'view_document_access_logs',
            'review_legal_aspects': 'review_and_approve_legal_aspects_of_plans',
            'view_contractual_obligations': 'view_contractual_obligations'
        }
        
        permission_field = compliance_permissions.get(permission_type)
        if permission_field:
            return RBACTPRMUtils.check_permission(user_id, permission_field)
        else:
            logger.warning(f"[RBAC TPRM] Unknown compliance permission type: {permission_type}")
            return False
    
    @staticmethod
    def check_bcp_drp_permission(user_id, permission_type):
        """Check BCP/DRP-related permissions"""
        bcp_drp_permissions = {
            'create_strategy': 'create_bcp_drp_strategy_and_plans',
            'view_plans': 'view_plans_and_documents',
            'assign_evaluation': 'assign_plans_for_evaluation',
            'approve_evaluations': 'approve_or_reject_plan_evaluations',
            'ocr_extraction': 'ocr_extraction_and_review',
            'create_questionnaire': 'create_questionnaire_for_testing',
            'review_answers': 'review_questionnaire_answers',
            'final_approval': 'final_approval_of_plan',
            'view_plan_status': 'view_bcp_drp_plan_status'
        }
        
        permission_field = bcp_drp_permissions.get(permission_type)
        if permission_field:
            return RBACTPRMUtils.check_permission(user_id, permission_field)
        else:
            logger.warning(f"[RBAC TPRM] Unknown BCP/DRP permission type: {permission_type}")
            return False
    
    @staticmethod
    def get_user_permissions_summary(user_id):
        """
        Get a comprehensive summary of user permissions organized by module
        
        Args:
            user_id: User ID to get permissions for
        
        Returns:
            dict: Organized permissions summary
        """
        try:
            rbac_record = RBACTPRMUtils.get_user_rbac_record(user_id)
            if not rbac_record:
                return None
            
            # Get all boolean fields (permissions)
            permission_fields = [field.name for field in RBACTPRM._meta.fields 
                               if isinstance(field, models.BooleanField)]
            
            permissions_summary = {
                'user_id': user_id,
                'username': rbac_record.username,
                'role': rbac_record.role,
                'modules': {
                    'rfp': {},
                    'contract': {},
                    'vendor': {},
                    'risk': {},
                    'compliance': {},
                    'bcp_drp': {},
                    'system': {}
                }
            }
            
            # Categorize permissions by module
            for field in permission_fields:
                value = getattr(rbac_record, field)
                if value:  # Only include True permissions
                    if 'rfp' in field.lower():
                        permissions_summary['modules']['rfp'][field] = True
                    elif 'contract' in field.lower():
                        permissions_summary['modules']['contract'][field] = True
                    elif 'vendor' in field.lower():
                        permissions_summary['modules']['vendor'][field] = True
                    elif 'risk' in field.lower():
                        permissions_summary['modules']['risk'][field] = True
                    elif 'compliance' in field.lower() or 'audit' in field.lower():
                        permissions_summary['modules']['compliance'][field] = True
                    elif 'bcp' in field.lower() or 'drp' in field.lower():
                        permissions_summary['modules']['bcp_drp'][field] = True
                    else:
                        permissions_summary['modules']['system'][field] = True
            
            return permissions_summary
            
        except Exception as e:
            logger.error(f"[RBAC TPRM] Error getting permissions summary for user {user_id}: {e}")
            return None
    
    @staticmethod
    def has_module_access(user_id, module_name):
        """
        Check if user has access to a specific module
        
        Args:
            user_id: User ID to check
            module_name: Name of the module ('rfp', 'contract', 'vendor', 'risk', 'compliance', 'bcp_drp')
        
        Returns:
            bool: True if user has any permission in the module
        """
        try:
            rbac_record = RBACTPRMUtils.get_user_rbac_record(user_id)
            if not rbac_record:
                return False
            
            # Check if user has any permission in the module by looking at actual permission fields
            if module_name == 'rfp':
                # Check for any RFP-related permission (using actual model field names, not db_column names)
                rfp_permissions = ['view_rfp', 'create_rfp', 'edit_rfp', 'delete_rfp', 'clone_rfp']
                return any(getattr(rbac_record, perm, False) for perm in rfp_permissions)
            elif module_name == 'contract':
                # Check for any Contract-related permission (using model field names)
                contract_permissions = ['list_contracts', 'create_contract', 'update_contract', 'delete_contract']
                return any(getattr(rbac_record, perm, False) for perm in contract_permissions)
            elif module_name == 'vendor':
                # Check for any Vendor-related permission (using model field names)
                vendor_permissions = ['view_vendors', 'create_vendor', 'update_vendor', 'delete_vendor']
                return any(getattr(rbac_record, perm, False) for perm in vendor_permissions)
            elif module_name == 'risk':
                # Check for any Risk-related permission (using model field names)
                risk_permissions = ['view_risk_assessments', 'create_risk_assessments']
                return any(getattr(rbac_record, perm, False) for perm in risk_permissions)
            elif module_name == 'compliance':
                # Check for any Compliance-related permission (using model field names)
                compliance_permissions = ['view_compliance_status_of_plans', 'generate_compliance_audit_reports']
                return any(getattr(rbac_record, perm, False) for perm in compliance_permissions)
            elif module_name == 'bcp_drp':
                # Check for any BCP/DRP-related permission (using model field names)
                bcp_drp_permissions = ['view_plans_and_documents', 'create_bcp_drp_strategy_and_plans']
                return any(getattr(rbac_record, perm, False) for perm in bcp_drp_permissions)
            else:
                logger.warning(f"[RBAC TPRM] Unknown module: {module_name}")
                return False
                
        except Exception as e:
            logger.error(f"[RBAC TPRM] Error checking module access for user {user_id}: {e}")
            return False
    
    @staticmethod
    def get_model_field_name_from_db_column(db_column_name):
        """
        Convert database column name (PascalCase) to model field name (snake_case)
        
        Args:
            db_column_name: Database column name like 'ViewRFP', 'CreateRFP'
            
        Returns:
            str: Model field name like 'view_rfp', 'create_rfp'
        """
        # Create a mapping from database column names to model field names
        column_to_field_mapping = {
            # RFP permissions
            'ViewRFP': 'view_rfp',
            'CreateRFP': 'create_rfp',
            'EditRFP': 'edit_rfp',
            'DeleteRFP': 'delete_rfp',
            'CloneRFP': 'clone_rfp',
            'SubmitRFPForReview': 'submit_rfp_for_review',
            'ApproveRFP': 'approve_rfp',
            'RejectRFP': 'reject_rfp',
            'AssignRFPReviewers': 'assign_rfp_reviewers',
            'ViewRFPApprovalStatus': 'view_rfp_approval_status',
            'ViewRFPVersions': 'view_rfp_versions',
            'CreateRFPVersion': 'create_rfp_version',
            'EditRFPVersion': 'edit_rfp_version',
            'ViewRFPVersion': 'view_rfp_version',
            
            # Contract permissions
            'ListContracts': 'list_contracts',
            'CreateContract': 'create_contract',
            'UpdateContract': 'update_contract',
            'DeleteContract': 'delete_contract',
            'ApproveContract': 'approve_contract',
            'RejectContract': 'reject_contract',
            
            # Vendor permissions
            'ViewVendors': 'view_vendors',
            'CreateVendor': 'create_vendor',
            'UpdateVendor': 'update_vendor',
            'DeleteVendor': 'delete_vendor',
            'SubmitVendorForApproval': 'submit_vendor_for_approval',
            'ApproveRejectVendor': 'approve_reject_vendor',
            'ViewRiskProfile': 'view_risk_profile',
            'ViewLifecycleHistory': 'view_lifecycle_history',
            'AssignQuestionnaires': 'assign_questionnaires',
            'SubmitQuestionnaireResponses': 'submit_questionnaire_responses',
            'ReviewApproveResponses': 'review_approve_responses',
            'ViewRiskAssessments': 'view_risk_assessments',
            'CreateRiskAssessments': 'create_risk_assessments',
            'AssessVendorRisk': 'assess_vendor_risk',
            'ViewVendorRiskScores': 'view_vendor_risk_scores',
            'InitiateScreening': 'initiate_screening',
            'ResolveScreeningMatches': 'resolve_screening_matches',
            'ViewScreeningResults': 'view_screening_results',
            
            # Risk permissions
            'ViewRiskAssessments': 'view_risk_assessments',
            'CreateRiskAssessments': 'create_risk_assessments',
            
            # Compliance permissions
            'ViewComplianceStatusOfPlans': 'view_compliance_status_of_plans',
            'GenerateComplianceAuditReports': 'generate_compliance_audit_reports',
            
            # BCP/DRP permissions
            'ViewPlansAndDocuments': 'view_plans_and_documents',
            'CreateBCPDRPStrategyAndPlans': 'create_bcp_drp_strategy_and_plans',
        }
        
        return column_to_field_mapping.get(db_column_name, db_column_name.lower())
    
    @staticmethod
    def debug_permission_check(user_id, permission_name, module_name):
        """
        Debug helper for permission checks
        
        Args:
            user_id: User ID being checked
            permission_name: Name of the permission being checked
            module_name: Name of the module
        """
        try:
            rbac_record = RBACTPRMUtils.get_user_rbac_record(user_id)
            if rbac_record:
                logger.debug(f"[RBAC TPRM DEBUG] User {user_id} ({rbac_record.username}) - "
                           f"Role: {rbac_record.role}, Module: {module_name}, "
                           f"Permission: {permission_name}")
            else:
                logger.debug(f"[RBAC TPRM DEBUG] User {user_id} - No RBAC record found")
        except Exception as e:
            logger.error(f"[RBAC TPRM DEBUG] Error in debug_permission_check: {e}")

    @staticmethod
    def is_vendor_user(user_id):
        """
        Check if the user has a Vendor role
       
        Args:
            user_id: User ID to check
       
        Returns:
            bool: True if user has Vendor role, False otherwise
        """
        try:
            rbac_record = RBACTPRMUtils.get_user_rbac_record(user_id)
            if rbac_record and rbac_record.role:
                is_vendor = rbac_record.role.lower() == 'vendor'
                logger.info(f"[RBAC TPRM] User {user_id} is_vendor: {is_vendor} (role: {rbac_record.role})")
                return is_vendor
            return False
        except Exception as e:
            logger.error(f"[RBAC TPRM] Error checking if user {user_id} is vendor: {e}")
            return False
   
    @staticmethod
    def get_vendor_info_for_user(user_id):
        """
        Get vendor information for a user if they have a Vendor role
       
        Args:
            user_id: User ID to check
       
        Returns:
            dict: Vendor information {'vendor_id': int, 'company_name': str} or None
        """
        try:
            rbac_record = RBACTPRMUtils.get_user_rbac_record(user_id)
           
            if not rbac_record:
                logger.warning(f"[RBAC TPRM] No RBAC record found for user {user_id}")
                return None
           
            # Check if user is a vendor
            if not RBACTPRMUtils.is_vendor_user(user_id):
                logger.info(f"[RBAC TPRM] User {user_id} is not a vendor (role: {rbac_record.role})")
                return None
           
            # Get username from RBAC record
            username = rbac_record.username
            logger.info(f"[RBAC TPRM] Looking for vendor with company_name matching username: {username}")
           
            # Query vendors table to find vendor with matching company_name
            try:
                from contracts.models import Vendor
                vendor = Vendor.objects.filter(company_name=username).first()
               
                if vendor:
                    logger.info(f"[RBAC TPRM] Found vendor for user {user_id}: vendor_id={vendor.vendor_id}, company_name={vendor.company_name}")
                    return {
                        'vendor_id': vendor.vendor_id,
                        'company_name': vendor.company_name,
                        'vendor_code': vendor.vendor_code
                    }
                else:
                    logger.warning(f"[RBAC TPRM] No vendor found with company_name={username} for user {user_id}")
                    return None
                   
            except Exception as e:
                logger.error(f"[RBAC TPRM] Error querying vendors table for user {user_id}: {e}")
                return None
               
        except Exception as e:
            logger.error(f"[RBAC TPRM] Error getting vendor info for user {user_id}: {e}")
            return None
   
    @staticmethod
    def get_username_from_user_id(user_id):
        """
        Get username from user_id via RBAC record
       
        Args:
            user_id: User ID to lookup
       
        Returns:
            str: Username or None
        """
        try:
            rbac_record = RBACTPRMUtils.get_user_rbac_record(user_id)
            if rbac_record:
                return rbac_record.username
            return None
        except Exception as e:
            logger.error(f"[RBAC TPRM] Error getting username for user {user_id}: {e}")
            return None
   
    @staticmethod
    def get_user_role(user_id):
        """
        Get role for a user
       
        Args:
            user_id: User ID to check
       
        Returns:
            str: Role name or None
        """
        try:
            rbac_record = RBACTPRMUtils.get_user_rbac_record(user_id)
            if rbac_record:
                return rbac_record.role
            return None
        except Exception as e:
            logger.error(f"[RBAC TPRM] Error getting role for user {user_id}: {e}")
            return None