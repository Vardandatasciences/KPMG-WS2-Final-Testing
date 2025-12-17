"""
Cross-Framework Mapping Service
Automatically checks evidence against multiple frameworks when uploaded for one framework
"""
import logging
from django.db import transaction
from django.conf import settings
from ...models import (
    Framework, AuditDocument, AuditDocumentMapping, Compliance, 
    Policy, SubPolicy
)
from ..Audit.ai_audit_api import (
    extract_text_from_document, 
    _get_policy_requirements,
    _process_single_requirement_batch,
    _determine_status
)
from django.db import connection
import os
import json

logger = logging.getLogger(__name__)


class CrossFrameworkMappingService:
    """Service to check evidence against multiple frameworks"""
    
    @staticmethod
    def get_active_frameworks(exclude_framework_id=None):
        """Get all active frameworks, optionally excluding one"""
        frameworks = Framework.objects.filter(
            Status='Approved',
            ActiveInactive='Active'
        )
        
        if exclude_framework_id:
            frameworks = frameworks.exclude(FrameworkId=exclude_framework_id)
        
        return frameworks.order_by('FrameworkName')
    
    @staticmethod
    def extract_document_text(document_path, doc_type):
        """Extract text from document"""
        try:
            # Get full file path
            if os.path.isabs(document_path):
                full_path = document_path
            else:
                full_path = os.path.join(settings.MEDIA_ROOT, document_path)
            
            if not os.path.exists(full_path):
                raise Exception(f"File not found: {full_path}")
            
            # Extract text using existing function
            full_text = extract_text_from_document(full_path, doc_type)
            
            if not full_text or len(full_text.strip()) < 50:
                raise Exception("Document has insufficient text for AI analysis")
            
            return full_text
        except Exception as e:
            logger.error(f"Error extracting document text: {e}")
            raise
    
    @staticmethod
    def get_framework_requirements(framework_id):
        """Get all compliance requirements for a framework"""
        try:
            # Get all policies for the framework
            policies = Policy.objects.filter(FrameworkId=framework_id)
            
            requirements = []
            for policy in policies:
                # Get subpolicies for this policy
                subpolicies = SubPolicy.objects.filter(PolicyId=policy.PolicyId)
                
                for subpolicy in subpolicies:
                    # Use existing function to get requirements for this policy/subpolicy
                    try:
                        policy_reqs = _get_policy_requirements(policy.PolicyId, subpolicy.SubPolicyId)
                        for req in policy_reqs:
                            req['framework_id'] = framework_id
                            req['framework_name'] = policy.FrameworkId.FrameworkName if policy.FrameworkId else ''
                            req['policy_id'] = policy.PolicyId
                            req['subpolicy_id'] = subpolicy.SubPolicyId
                            requirements.append(req)
                    except Exception as e:
                        logger.warning(f"Error getting requirements for policy {policy.PolicyId}, subpolicy {subpolicy.SubPolicyId}: {e}")
                        # Fallback: get compliances directly
                        compliances = Compliance.objects.filter(SubPolicyId=subpolicy.SubPolicyId)
                        for compliance in compliances:
                            requirements.append({
                                'compliance_id': compliance.ComplianceId,
                                'title': compliance.ComplianceTitle or compliance.Identifier or f"Compliance {compliance.ComplianceId}",
                                'description': compliance.ComplianceItemDescription or '',
                                'framework_id': framework_id,
                                'framework_name': policy.FrameworkId.FrameworkName if policy.FrameworkId else '',
                                'policy_id': policy.PolicyId,
                                'subpolicy_id': subpolicy.SubPolicyId
                            })
            
            return requirements
        except Exception as e:
            logger.error(f"Error getting framework requirements: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    @staticmethod
    def check_document_against_framework(document_text, document_name, framework_id, audit_id=None, document_id=None):
        """Check document compliance against a specific framework using AI"""
        try:
            logger.info(f"🔍 Checking document against framework {framework_id}")
            
            # Get requirements for this framework
            requirements = CrossFrameworkMappingService.get_framework_requirements(framework_id)
            
            if not requirements:
                logger.warning(f"No requirements found for framework {framework_id}")
                return {
                    'success': False,
                    'error': f'No compliance requirements found for framework {framework_id}',
                    'framework_id': framework_id,
                    'compliance_count': 0
                }
            
            # Limit to first 10 requirements for performance
            requirements = requirements[:10]
            
            logger.info(f"📋 Checking {len(requirements)} requirements for framework {framework_id}")
            
            # Process requirements using AI (similar to existing audit processing)
            analyses = []
            for idx, req in enumerate(requirements):
                try:
                    # Use existing AI processing function
                    batch_result = _process_single_requirement_batch(
                        document_text,
                        [req],
                        idx + 1,
                        audit_id=audit_id,
                        document_id=document_id
                    )
                    
                    if batch_result:
                        for analysis in batch_result:
                            analysis['framework_id'] = framework_id
                            analysis['compliance_id'] = req['compliance_id']
                            analyses.append(analysis)
                except Exception as e:
                    logger.error(f"Error processing requirement {idx + 1}: {e}")
                    continue
            
            if not analyses:
                return {
                    'success': False,
                    'error': 'No compliance analysis results generated',
                    'framework_id': framework_id
                }
            
            # Calculate overall status
            status_label, confidence = _determine_status(requirements, analyses)
            
            # Count compliance statuses
            compliant_count = sum(1 for a in analyses if a.get('status') == 'compliant')
            partially_compliant_count = sum(1 for a in analyses if a.get('status') == 'partially_compliant')
            non_compliant_count = sum(1 for a in analyses if a.get('status') == 'non_compliant')
            
            return {
                'success': True,
                'framework_id': framework_id,
                'framework_name': requirements[0]['framework_name'] if requirements else '',
                'compliance_count': len(requirements),
                'analyses': analyses,
                'overall_status': status_label,
                'confidence': confidence,
                'compliant_count': compliant_count,
                'partially_compliant_count': partially_compliant_count,
                'non_compliant_count': non_compliant_count,
                'compliance_score': (compliant_count + partially_compliant_count * 0.5) / len(analyses) if analyses else 0
            }
            
        except Exception as e:
            logger.error(f"Error checking document against framework {framework_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'framework_id': framework_id
            }
    
    @staticmethod
    @transaction.atomic
    def check_document_against_multiple_frameworks(
        document_id, 
        primary_framework_id, 
        audit_id=None,
        target_framework_ids=None
    ):
        """
        Check a document against multiple frameworks
        
        Args:
            document_id: ID of the uploaded document
            primary_framework_id: Framework the document was originally uploaded for
            audit_id: Optional audit ID
            target_framework_ids: Optional list of specific framework IDs to check. 
                                 If None, checks all active frameworks except primary
        """
        try:
            logger.info(f"🔄 Starting cross-framework check for document {document_id}")
            
            # Get the document
            try:
                document = AuditDocument.objects.get(DocumentId=document_id)
            except AuditDocument.DoesNotExist:
                return {
                    'success': False,
                    'error': f'Document {document_id} not found'
                }
            
            # Get document text
            try:
                doc_type = document.DocumentType or document.MimeType or 'application/pdf'
                document_text = CrossFrameworkMappingService.extract_document_text(
                    document.DocumentPath,
                    doc_type
                )
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Error extracting document text: {str(e)}'
                }
            
            # Determine which frameworks to check
            if target_framework_ids:
                frameworks_to_check = Framework.objects.filter(
                    FrameworkId__in=target_framework_ids
                ).exclude(FrameworkId=primary_framework_id)
            else:
                frameworks_to_check = CrossFrameworkMappingService.get_active_frameworks(
                    exclude_framework_id=primary_framework_id
                )
            
            logger.info(f"📊 Checking document against {frameworks_to_check.count()} frameworks")
            
            # Check against each framework
            results = []
            mappings_created = []
            
            for framework in frameworks_to_check:
                logger.info(f"🔍 Checking framework: {framework.FrameworkName} (ID: {framework.FrameworkId})")
                
                # Check compliance
                check_result = CrossFrameworkMappingService.check_document_against_framework(
                    document_text,
                    document.DocumentName,
                    framework.FrameworkId,
                    audit_id=audit_id,
                    document_id=document_id
                )
                
                if check_result['success']:
                    # Store mappings for each compliance requirement
                    for analysis in check_result.get('analyses', []):
                        compliance_id = analysis.get('compliance_id')
                        if not compliance_id:
                            continue
                        
                        try:
                            # Check if mapping already exists (considering unique_together constraint on DocumentId+ComplianceId)
                            # Since FrameworkId is not in unique_together, we need to check by all three fields
                            existing_mapping = AuditDocumentMapping.objects.filter(
                                DocumentId=document_id,
                                ComplianceId=compliance_id,
                                FrameworkId=framework.FrameworkId
                            ).first()
                            
                            if existing_mapping:
                                # Update existing mapping
                                existing_mapping.ComplianceStatus = analysis.get('status', 'requires_review')
                                existing_mapping.ConfidenceScore = analysis.get('confidence', 0.0)
                                existing_mapping.AIRecommendations = json.dumps(analysis.get('recommendations', []))
                                existing_mapping.RiskLevel = analysis.get('risk_level', 'medium').lower()
                                existing_mapping.FrameworkId_id = framework.FrameworkId  # Ensure FrameworkId is set
                                existing_mapping.save()
                                mappings_created.append(existing_mapping.MappingId)
                            else:
                                # Check if there's a mapping with same DocumentId+ComplianceId but different FrameworkId
                                # If so, we'll create a new one with the new FrameworkId
                                # Note: This may require database migration to add FrameworkId to unique_together
                                # For now, we'll try to create and handle any constraint errors
                                try:
                                    new_mapping = AuditDocumentMapping.objects.create(
                                        DocumentId_id=document_id,
                                        ComplianceId_id=compliance_id,
                                        FrameworkId_id=framework.FrameworkId,
                                        ComplianceStatus=analysis.get('status', 'requires_review'),
                                        ConfidenceScore=analysis.get('confidence', 0.0),
                                        AIRecommendations=json.dumps(analysis.get('recommendations', [])),
                                        RiskLevel=analysis.get('risk_level', 'medium').lower(),
                                        SectionContent=json.dumps(analysis.get('evidence', []))[:500] if analysis.get('evidence') else None
                                    )
                                    mappings_created.append(new_mapping.MappingId)
                                except Exception as create_error:
                                    # If creation fails due to unique constraint, try to update existing one
                                    logger.warning(f"Creation failed, trying to update existing mapping: {create_error}")
                                    existing_by_doc_compliance = AuditDocumentMapping.objects.filter(
                                        DocumentId=document_id,
                                        ComplianceId=compliance_id
                                    ).first()
                                    if existing_by_doc_compliance:
                                        existing_by_doc_compliance.FrameworkId_id = framework.FrameworkId
                                        existing_by_doc_compliance.ComplianceStatus = analysis.get('status', 'requires_review')
                                        existing_by_doc_compliance.ConfidenceScore = analysis.get('confidence', 0.0)
                                        existing_by_doc_compliance.AIRecommendations = json.dumps(analysis.get('recommendations', []))
                                        existing_by_doc_compliance.RiskLevel = analysis.get('risk_level', 'medium').lower()
                                        existing_by_doc_compliance.save()
                                        mappings_created.append(existing_by_doc_compliance.MappingId)
                        except Exception as e:
                            logger.error(f"Error creating/updating mapping for compliance {compliance_id}: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                            continue
                    
                    results.append({
                        'framework_id': framework.FrameworkId,
                        'framework_name': framework.FrameworkName,
                        'compliance_count': check_result.get('compliance_count', 0),
                        'compliant_count': check_result.get('compliant_count', 0),
                        'partially_compliant_count': check_result.get('partially_compliant_count', 0),
                        'non_compliant_count': check_result.get('non_compliant_count', 0),
                        'overall_status': check_result.get('overall_status', 'unknown'),
                        'confidence': check_result.get('confidence', 0.0),
                        'compliance_score': check_result.get('compliance_score', 0.0)
                    })
                else:
                    logger.warning(f"Failed to check framework {framework.FrameworkId}: {check_result.get('error')}")
                    results.append({
                        'framework_id': framework.FrameworkId,
                        'framework_name': framework.FrameworkName,
                        'error': check_result.get('error', 'Unknown error'),
                        'success': False
                    })
            
            return {
                'success': True,
                'document_id': document_id,
                'document_name': document.DocumentName,
                'primary_framework_id': primary_framework_id,
                'frameworks_checked': len(results),
                'mappings_created': len(mappings_created),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in cross-framework check: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }

