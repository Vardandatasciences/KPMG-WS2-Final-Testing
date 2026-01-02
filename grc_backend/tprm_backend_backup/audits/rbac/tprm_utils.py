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
        
        # Try JWT authentication first
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
                # Use our custom JWT verification method
                import jwt
                from django.conf import settings
                from bcpdrp.models import Users
                
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('user_id')
                
                if user_id:
                    logger.info(f"[RBAC TPRM] Successfully extracted user_id from JWT: {user_id}")
                    return user_id
                else:
                    logger.warning("[RBAC TPRM] No user_id found in JWT payload")
                    
        except Exception as e:
            logger.error(f"[RBAC TPRM] Error extracting user_id from JWT: {e}")
        
        # Fallback to session authentication
        try:
            user_id = request.session.get('user_id')
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
    def get_user_rbac_record(user_id):
        """Get the RBAC TPRM record for a user with extensive debugging"""
        try:
            logger.debug(f"[RBAC TPRM] Looking up RBAC record for user_id: {user_id}")
            
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
    def check_permission(user_id, permission_name):
        """
        Check if user has a specific permission
        
        Args:
            user_id: User ID to check
            permission_name: Name of the permission field to check (can be either db_column name or model field name)
        
        Returns:
            bool: True if user has permission, False otherwise
        """
        try:
            rbac_record = RBACTPRMUtils.get_user_rbac_record(user_id)
            if not rbac_record:
                logger.warning(f"[RBAC TPRM] No RBAC record found for user {user_id}")
                return False
            
            # Convert database column name to model field name if needed
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
            
            # Full database column names
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
            'ViewRFPVersion': 'view_rfp_version'
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
            'RejectContractRenewal': 'reject_contract_renewal'
        }
        
        permission_field = contract_permissions.get(permission_type)
        if permission_field:
            return RBACTPRMUtils.check_permission(user_id, permission_field)
        else:
            logger.warning(f"[RBAC TPRM] Unknown contract permission type: {permission_type}")
            return False
    
    @staticmethod
    def check_vendor_permission(user_id, permission_type):
        """Check vendor-related permissions"""
        # Handle both simplified types and full database column names
        vendor_permissions = {
            # Simplified types
            'view': 'view_vendors',
            'create': 'create_vendor',
            'update': 'update_vendor',
            'delete': 'delete_vendor',
            'submit_approval': 'submit_vendor_for_approval',
            'approve_reject': 'approve_reject_vendor',
            'select_for_rfp': 'select_vendors_for_rfp',
            'invite_for_rfp': 'invite_vendors_for_rfp',
            'track_invitations': 'track_rfp_invitations',
            'assess_risk': 'assess_vendor_risk',
            'view_risk_scores': 'view_vendor_risk_scores',
            
            # Full database column names
            'ViewVendors': 'view_vendors',
            'CreateVendor': 'create_vendor',
            'UpdateVendor': 'update_vendor',
            'DeleteVendor': 'delete_vendor',
            'SubmitVendorForApproval': 'submit_vendor_for_approval',
            'ApproveRejectVendor': 'approve_reject_vendor',
            'SelectVendorsForRFP': 'select_vendors_for_rfp',
            'InviteVendorsForRFP': 'invite_vendors_for_rfp',
            'TrackRFPInvitations': 'track_rfp_invitations',
            'AssessVendorRisk': 'assess_vendor_risk',
            'ViewVendorRiskScores': 'view_vendor_risk_scores'
        }
        
        permission_field = vendor_permissions.get(permission_type)
        if permission_field:
            return RBACTPRMUtils.check_permission(user_id, permission_field)
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
        else:
            logger.warning(f"[RBAC TPRM] Unknown risk permission type: {permission_type}")
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
        # Map permission types to actual field names in the RBAC model
        bcp_drp_permissions = {
            # Direct field name mappings (as used in views)
            'ViewPlansAndDocuments': 'view_plans_and_documents',
            'CreateBCPDRPStrategyAndPlans': 'create_bcp_drp_strategy_and_plans',
            'AssignPlansForEvaluation': 'assign_plans_for_evaluation',
            'ApproveOrRejectPlanEvaluations': 'approve_or_reject_plan_evaluations',
            'OCRExtractionAndReview': 'ocr_extraction_and_review',
            'CreateQuestionnaireForTesting': 'create_questionnaire_for_testing',
            'ViewAllQuestionnaires': 'view_all_questionnaires',
            'AssignQuestionnairesForReview': 'assign_questionnaires_for_review',
            'ReviewQuestionnaireAnswers': 'review_questionnaire_answers',
            'FinalApprovalOfPlan': 'final_approval_of_plan',
            'CreateQuestionnaire': 'create_questionnaire_for_testing',  # Alias
            # Legacy mappings for backward compatibility
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
            logger.debug(f"[RBAC TPRM] Checking BCP/DRP permission: {permission_type} -> {permission_field}")
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
