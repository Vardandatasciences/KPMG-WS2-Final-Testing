"""
Organizational Controls API
Handles CRUD operations and AI audit for organizational controls mapping
"""

import json
import os
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import connection, transaction
from django.conf import settings

from rest_framework.decorators import api_view, permission_classes, authentication_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from django.db import models as db_models

from ...models import (
    OrganizationalControl, OrganizationalControlDocument, Framework, Policy, SubPolicy, Compliance, Users
)
from ...rbac.utils import RBACUtils

# MULTI-TENANCY: Import tenant utilities for data isolation
from ...tenant_utils import (
    require_tenant, tenant_filter, get_tenant_id_from_request,
    validate_tenant_access, get_tenant_aware_queryset
)
from ..Audit.ai_audit_api import call_ai_api

logger = logging.getLogger(__name__)


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


def extract_text_from_document(file_path, file_extension):
    """
    Extract text content from uploaded document
    """
    extracted_text = ""
    
    try:
        if file_extension in ['.txt']:
            with open(file_path, 'r', encoding='utf-8') as f:
                extracted_text = f.read()
                
        elif file_extension in ['.pdf']:
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        extracted_text += page.extract_text() + "\n"
            except ImportError:
                logger.warning("PyPDF2 not installed, cannot extract PDF text")
                
        elif file_extension in ['.docx']:
            try:
                from docx import Document
                doc = Document(file_path)
                for para in doc.paragraphs:
                    extracted_text += para.text + "\n"
            except ImportError:
                logger.warning("python-docx not installed, cannot extract DOCX text")
                
        elif file_extension in ['.doc']:
            logger.warning("DOC format not supported, please use DOCX")
            
    except Exception as e:
        logger.error(f"Error extracting text from document: {e}")
        
    return extracted_text.strip()


# ==================== HELPER: Check if table exists ====================
def table_exists(cursor, table_name):
    """Check if a table exists in the database"""
    try:
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        return cursor.fetchone() is not None
    except:
        return False


# ==================== GET FRAMEWORK CONTROLS (Hierarchical) ====================
@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_framework_controls(request, framework_id):
    """
    Get all controls for a framework organized by Policy > SubPolicy > Compliance
    with organizational control mapping status (if table exists)
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        with connection.cursor() as cursor:
            # Check if organizational_controls table exists
            org_controls_exists = table_exists(cursor, 'organizational_controls')
            
            # Get all policies for framework
            cursor.execute("""
                SELECT PolicyId, PolicyName, Identifier 
                FROM policies 
                WHERE FrameworkId = %s
                ORDER BY Identifier, PolicyName
            """, [framework_id])
            policies = cursor.fetchall()
            
            result = []
            
            for policy in policies:
                policy_id, policy_name, policy_identifier = policy
                
                # Get subpolicies for this policy
                cursor.execute("""
                    SELECT SubPolicyId, SubPolicyName, Identifier, Description
                    FROM subpolicies 
                    WHERE PolicyId = %s
                    ORDER BY Identifier, SubPolicyName
                """, [policy_id])
                subpolicies = cursor.fetchall()
                
                subpolicy_list = []
                for subpolicy in subpolicies:
                    sp_id, sp_name, sp_identifier, sp_desc = subpolicy
                    
                    # Get compliances (controls) for this subpolicy
                    if org_controls_exists:
                        # Join with organizational_controls if table exists
                        cursor.execute("""
                            SELECT c.ComplianceId, c.ComplianceTitle, c.ComplianceItemDescription, 
                                   c.Identifier, c.MandatoryOptional, c.Criticality,
                                   oc.OrgControlId, oc.MappingStatus, oc.ControlText, 
                                   oc.AIAnalysis, oc.ConfidenceScore
                            FROM compliance c
                            LEFT JOIN organizational_controls oc ON c.ComplianceId = oc.ComplianceId
                            WHERE c.SubPolicyId = %s
                            ORDER BY c.Identifier, c.ComplianceTitle
                        """, [sp_id])
                        compliances = cursor.fetchall()
                        
                        compliance_list = []
                        for comp in compliances:
                            ai_analysis = comp[9] if comp[9] else {}
                            if isinstance(ai_analysis, str):
                                try:
                                    ai_analysis = json.loads(ai_analysis)
                                except:
                                    ai_analysis = {}
                            
                            # Get primary document name if exists
                            document_name = None
                            if comp[6]:  # If OrgControlId exists
                                primary_doc = OrganizationalControlDocument.objects.filter(
                                    OrgControlId_id=comp[6], IsPrimary=True
                                ).first()
                                if primary_doc:
                                    document_name = primary_doc.DocumentName
                            
                            compliance_list.append({
                                'ComplianceId': comp[0],
                                'ComplianceTitle': comp[1],
                                'ComplianceItemDescription': comp[2],
                                'Identifier': comp[3],
                                'MandatoryOptional': comp[4],
                                'Criticality': comp[5],
                                'OrgControlId': comp[6],
                                'MappingStatus': comp[7] or 'not_audited',
                                'ControlText': comp[8],
                                'DocumentName': document_name,
                                'AIAnalysis': ai_analysis,
                                'WhatIsSatisfying': ai_analysis.get('what_is_satisfying'),
                                'WhatIsLeft': ai_analysis.get('what_is_left'),
                                'WhyNotMapped': ai_analysis.get('why_not_mapped'),
                                'ConfidenceScore': comp[10]
                            })
                    else:
                        # Just get compliances without org control data
                        cursor.execute("""
                            SELECT ComplianceId, ComplianceTitle, ComplianceItemDescription, 
                                   Identifier, MandatoryOptional, Criticality
                            FROM compliance 
                            WHERE SubPolicyId = %s
                            ORDER BY Identifier, ComplianceTitle
                        """, [sp_id])
                        compliances = cursor.fetchall()
                        
                        compliance_list = []
                        for comp in compliances:
                            compliance_list.append({
                                'ComplianceId': comp[0],
                                'ComplianceTitle': comp[1],
                                'ComplianceItemDescription': comp[2],
                                'Identifier': comp[3],
                                'MandatoryOptional': comp[4],
                                'Criticality': comp[5],
                                'OrgControlId': None,
                                'MappingStatus': 'not_audited',
                                'ControlText': None,
                                'DocumentName': None,
                                'AIAnalysis': None,
                                'WhatIsSatisfying': None,
                                'WhatIsLeft': None,
                                'WhyNotMapped': None,
                                'ConfidenceScore': None
                            })
                    
                    subpolicy_list.append({
                        'SubPolicyId': sp_id,
                        'SubPolicyName': sp_name,
                        'Identifier': sp_identifier,
                        'Description': sp_desc,
                        'Compliances': compliance_list
                    })
                
                result.append({
                    'PolicyId': policy_id,
                    'PolicyName': policy_name,
                    'Identifier': policy_identifier,
                    'SubPolicies': subpolicy_list
                })
            
            return Response({
                'success': True,
                'frameworkId': framework_id,
                'controls': result
            })
            
    except Exception as e:
        logger.error(f"Error getting framework controls: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== GET SINGLE ORGANIZATIONAL CONTROL ====================
@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_organizational_control(request, compliance_id):
    """
    Get organizational control details for a specific compliance
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT oc.OrgControlId, oc.ControlText, oc.ExtractedText, oc.MappingStatus, 
                       oc.AIAnalysis, oc.ConfidenceScore,
                       oc.CreatedAt, oc.UpdatedAt, oc.LastAuditedAt,
                       c.ComplianceTitle, c.ComplianceItemDescription, c.Identifier
                FROM organizational_controls oc
                JOIN compliance c ON oc.ComplianceId = c.ComplianceId
                WHERE oc.ComplianceId = %s
            """, [compliance_id])
            
            row = cursor.fetchone()
            
            if row:
                # Parse AIAnalysis JSON
                ai_analysis = row[4] if row[4] else {}
                if isinstance(ai_analysis, str):
                    try:
                        ai_analysis = json.loads(ai_analysis)
                    except:
                        ai_analysis = {}
                
                # Get documents for this org control
                documents = []
                if row[0]:  # If OrgControlId exists
                    org_docs = OrganizationalControlDocument.objects.filter(
                        OrgControlId_id=row[0]
                    ).order_by('-IsPrimary', '-UploadedAt')
                    documents = [{
                        'DocumentId': doc.DocumentId,
                        'DocumentName': doc.DocumentName,
                        'DocumentPath': doc.DocumentPath,
                        'DocumentType': doc.DocumentType,
                        'FileSize': doc.FileSize,
                        'UploadedAt': doc.UploadedAt.isoformat() if doc.UploadedAt else None,
                        'IsPrimary': doc.IsPrimary
                    } for doc in org_docs]
                
                return Response({
                    'success': True,
                    'org_control': {
                        'OrgControlId': row[0],
                        'ControlText': row[1],
                        'ExtractedText': row[2],
                        'MappingStatus': row[3],
                        'AIAnalysis': ai_analysis,
                        'WhatIsSatisfying': ai_analysis.get('what_is_satisfying'),
                        'WhatIsLeft': ai_analysis.get('what_is_left'),
                        'WhyNotMapped': ai_analysis.get('why_not_mapped'),
                        'ConfidenceScore': row[5],
                        'CreatedAt': row[6].isoformat() if row[6] else None,
                        'UpdatedAt': row[7].isoformat() if row[7] else None,
                        'LastAuditedAt': row[8].isoformat() if row[8] else None,
                        'ComplianceTitle': row[9],
                        'ComplianceItemDescription': row[10],
                        'ComplianceIdentifier': row[11],
                        'Documents': documents
                    }
                })
            else:
                return Response({
                    'success': True,
                    'org_control': None,
                    'message': 'No organizational control found for this compliance'
                })
                
    except Exception as e:
        logger.error(f"Error getting organizational control: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== SAVE ORGANIZATIONAL CONTROL (Manual Entry) ====================
@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def save_organizational_control(request):
    """
    Save organizational control text for a specific compliance
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        data = request.data
        compliance_id = data.get('compliance_id')
        control_text = data.get('control_text')
        framework_id = data.get('framework_id')
        
        if not compliance_id or not control_text:
            return Response({
                'success': False,
                'error': 'compliance_id and control_text are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = RBACUtils.get_user_id_from_request(request)
        
        # Check if organizational control already exists for this compliance
        org_control = OrganizationalControl.objects.filter(tenant_id=tenant_id, ComplianceId_id=compliance_id).first()
        
        if org_control:
            # Update existing
            org_control.ControlText = control_text
            org_control.MappingStatus = 'not_audited'  # Reset status for re-audit
            org_control.UpdatedAt = timezone.now()
            org_control.save()
        else:
            # Get compliance details
            compliance = Compliance.objects.get(ComplianceId=compliance_id, tenant_id=tenant_id)
            
            # Create new
            org_control = OrganizationalControl.objects.create(
                FrameworkId_id=framework_id or compliance.FrameworkId_id,
                PolicyId_id=compliance.SubPolicy.PolicyId_id,
                SubPolicyId_id=compliance.SubPolicy_id,
                ComplianceId_id=compliance_id,
                ControlText=control_text,
                MappingStatus='not_audited',
                CreatedBy_id=user_id
            )
        
        return Response({
            'success': True,
            'message': 'Organizational control saved successfully',
            'org_control_id': org_control.OrgControlId
        })
        
    except Compliance.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Compliance with ID {compliance_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error saving organizational control: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== UPLOAD ORGANIZATIONAL CONTROL DOCUMENT ====================
@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@parser_classes([MultiPartParser, FormParser])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def upload_organizational_document(request):
    """
    Upload organizational control document(s) for one or multiple compliances
    Supports multiple files upload
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        # Handle both single file and multiple files
        files = request.FILES.getlist('files') or request.FILES.getlist('file')
        if not files:
            logger.error(f"Upload failed: No files in request. FILES keys: {list(request.FILES.keys())}")
            return Response({
                'success': False,
                'error': 'No file(s) provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        framework_id = request.POST.get('framework_id')
        compliance_id = request.POST.get('compliance_id')
        compliance_ids_str = request.POST.get('compliance_ids', '')
        upload_type = request.POST.get('upload_type', 'single')  # single, policy, subpolicy, bulk
        upload_mode = request.POST.get('upload_mode', 'single')  # single, multiple, bulk
        policy_id = request.POST.get('policy_id')
        subpolicy_id = request.POST.get('subpolicy_id')
        
        # Parse compliance_ids - handle both single value and comma-separated string
        compliance_ids = []
        if compliance_id:
            compliance_ids = [compliance_id]
        elif compliance_ids_str:
            # Handle both single value and comma-separated string
            if ',' in compliance_ids_str:
                compliance_ids = [cid.strip() for cid in compliance_ids_str.split(',') if cid.strip()]
            else:
                # Single value provided as compliance_ids
                compliance_ids = [compliance_ids_str.strip()] if compliance_ids_str.strip() else []
        
        user_id = RBACUtils.get_user_id_from_request(request)
        
        # Determine which compliances to link documents to
        target_compliance_ids = []
        
        if upload_type == 'compliance' and compliance_id:
            target_compliance_ids = [compliance_id]
        elif upload_type == 'single':
            # For single upload, check both compliance_id and compliance_ids
            if compliance_id:
                target_compliance_ids = [compliance_id]
            elif compliance_ids:
                target_compliance_ids = compliance_ids
        elif upload_type == 'policy' and policy_id:
            # Get all compliances under this policy
            compliances = Compliance.objects.filter(tenant_id=tenant_id, 
                SubPolicy__PolicyId=policy_id
            ).values_list('ComplianceId', flat=True)
            target_compliance_ids = list(compliances)
            logger.info(f"Found {len(target_compliance_ids)} compliances for policy_id={policy_id}")
        elif upload_type == 'subpolicy' and subpolicy_id:
            # Get all compliances under this subpolicy
            compliances = Compliance.objects.filter(tenant_id=tenant_id, 
                SubPolicy=subpolicy_id
            ).values_list('ComplianceId', flat=True)
            target_compliance_ids = list(compliances)
            logger.info(f"Found {len(target_compliance_ids)} compliances for subpolicy_id={subpolicy_id}")
        elif (upload_type == 'bulk' or upload_type == 'framework') and framework_id:
            # Get all compliances under this framework
            compliances = Compliance.objects.filter(tenant_id=tenant_id, 
                SubPolicy__PolicyId__FrameworkId=framework_id
            ).values_list('ComplianceId', flat=True)
            target_compliance_ids = list(compliances)
            logger.info(f"Found {len(target_compliance_ids)} compliances for framework_id={framework_id}")
        
        if not target_compliance_ids:
            # Debug: Check if subpolicy exists and has compliances
            if upload_type == 'subpolicy' and subpolicy_id:
                try:
                    subpolicy = SubPolicy.objects.filter(tenant_id=tenant_id, SubPolicyId=subpolicy_id).first()
                    if subpolicy:
                        all_compliances = Compliance.objects.filter(tenant_id=tenant_id, SubPolicy=subpolicy_id)
                        logger.error(f"SubPolicy {subpolicy_id} exists but has {all_compliances.count()} compliances. "
                                   f"SubPolicy name: {subpolicy.SubPolicyName}")
                    else:
                        logger.error(f"SubPolicy {subpolicy_id} does not exist in database")
                except Exception as e:
                    logger.error(f"Error checking subpolicy: {e}")
            
            logger.error(f"Upload failed: No compliances found. upload_type={upload_type}, compliance_id={compliance_id}, "
                        f"compliance_ids={compliance_ids}, policy_id={policy_id}, subpolicy_id={subpolicy_id}, "
                        f"framework_id={framework_id}")
            return Response({
                'success': False,
                'error': f'No compliances found for the specified criteria. upload_type={upload_type}, '
                        f'compliance_id={compliance_id}, policy_id={policy_id}, subpolicy_id={subpolicy_id}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        bulk_upload_id = str(uuid.uuid4()) if len(target_compliance_ids) > 1 else None
        created_controls = []
        all_extracted_texts = []
        
        # Process each file
        for file in files:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.name)[1].lower()
            unique_filename = f"{file_id}{file_extension}"
            
            # Save file
            file_path = os.path.join('org_control_documents', unique_filename)
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            logger.info(f"File saved to: {full_path}")
            
            # Extract text from document
            extracted_text = extract_text_from_document(full_path, file_extension)
            all_extracted_texts.append(extracted_text)
            
            # Process each compliance
            for comp_id in target_compliance_ids:
                try:
                    compliance = Compliance.objects.get(ComplianceId=comp_id, tenant_id=tenant_id)
                    
                    # Get or create org control
                    org_control = OrganizationalControl.objects.filter(tenant_id=tenant_id, ComplianceId_id=comp_id).first()
                    
                    if not org_control:
                        org_control = OrganizationalControl.objects.create(
                            FrameworkId_id=framework_id or compliance.FrameworkId_id,
                            PolicyId_id=compliance.SubPolicy.PolicyId_id,
                            SubPolicyId_id=compliance.SubPolicy_id,
                            ComplianceId_id=comp_id,
                            MappingStatus='not_audited',
                            BulkUploadId=bulk_upload_id,
                            CreatedBy_id=user_id
                        )
                        created_controls.append(org_control.OrgControlId)
                    else:
                        if org_control.OrgControlId not in created_controls:
                            created_controls.append(org_control.OrgControlId)
                    
                    # Check if this is the first document for this org control (make it primary)
                    is_first_doc = not OrganizationalControlDocument.objects.filter(
                        OrgControlId_id=org_control.OrgControlId
                    ).exists()
                    
                    # Create document record
                    doc = OrganizationalControlDocument.objects.create(
                        OrgControlId_id=org_control.OrgControlId,
                        DocumentName=file.name,
                        DocumentPath=file_path,
                        DocumentType=file_extension.replace('.', ''),
                        FileSize=file.size,
                        ExtractedText=extracted_text,
                        IsPrimary=is_first_doc,
                        UploadedBy_id=user_id
                    )
                    
                    # Update aggregated ExtractedText in org control
                    all_docs = OrganizationalControlDocument.objects.filter(
                        OrgControlId_id=org_control.OrgControlId
                    )
                    combined_text = '\n\n'.join([
                        doc.ExtractedText for doc in all_docs if doc.ExtractedText
                    ])
                    org_control.ExtractedText = combined_text
                    org_control.MappingStatus = 'not_audited'
                    org_control.BulkUploadId = bulk_upload_id
                    org_control.save()
                    
                except Exception as e:
                    logger.error(f"Error creating org control document for compliance {comp_id}: {e}")
        
        return Response({
            'success': True,
            'message': f'{len(files)} document(s) uploaded and linked to {len(set(created_controls))} compliance(s)',
            'org_control_ids': list(set(created_controls)),
            'bulk_upload_id': bulk_upload_id,
            'files_uploaded': len(files),
            'total_extracted_text_length': sum(len(text) for text in all_extracted_texts)
        })
        
    except Exception as e:
        logger.error(f"Error uploading organizational document: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== RUN AI AUDIT FOR CONTROL MAPPING ====================
@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def run_control_mapping_audit(request):
    """
    Run AI audit to check if organizational controls satisfy framework controls
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        data = request.data
        org_control_ids = data.get('org_control_ids', [])
        compliance_id = data.get('compliance_id')
        framework_id = data.get('framework_id')
        policy_id = data.get('policy_id')
        subpolicy_id = data.get('subpolicy_id')
        audit_all = data.get('audit_all', False)
        
        # Determine which controls to audit
        # Note: OrganizationalControl doesn't have tenant_id, so filter through related models that have tenant
        if compliance_id:
            # Single compliance audit - filter through Compliance.tenant
            org_controls = OrganizationalControl.objects.filter(
                ComplianceId_id=compliance_id,
                ComplianceId__tenant_id=tenant_id
            )
        elif policy_id:
            # Audit all compliances under this policy - filter through Policy.tenant or Compliance.tenant
            org_controls = OrganizationalControl.objects.filter(
                PolicyId_id=policy_id,
                PolicyId__tenant_id=tenant_id
            )
        elif subpolicy_id:
            # Audit all compliances under this subpolicy - filter through SubPolicy.tenant or Compliance.tenant
            org_controls = OrganizationalControl.objects.filter(
                SubPolicyId_id=subpolicy_id,
                SubPolicyId__tenant_id=tenant_id
            )
        elif audit_all and framework_id:
            # Audit all controls in framework - filter through Framework.tenant
            org_controls = OrganizationalControl.objects.filter(
                FrameworkId_id=framework_id,
                FrameworkId__tenant_id=tenant_id
            )
        elif org_control_ids:
            # Audit specific org control IDs - filter through Framework.tenant (most reliable since FrameworkId is always present)
            org_controls = OrganizationalControl.objects.filter(
                OrgControlId__in=org_control_ids,
                FrameworkId__tenant_id=tenant_id
            )
        else:
            return Response({
                'success': False,
                'error': 'Provide org_control_ids, compliance_id, policy_id, subpolicy_id, or framework_id with audit_all=true'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filter to only those that have content
        org_controls = org_controls.filter(
            db_models.Q(ControlText__isnull=False) | db_models.Q(ExtractedText__isnull=False)
        ).exclude(ControlText='', ExtractedText='')
        
        results = []
        
        for org_control in org_controls:
            try:
                # Get the framework compliance requirement
                compliance = Compliance.objects.get(ComplianceId=org_control.ComplianceId_id, tenant_id=tenant_id)
                
                # Prepare organizational control content
                org_content = org_control.ControlText or org_control.ExtractedText or ""
                
                if not org_content.strip():
                    results.append({
                        'org_control_id': org_control.OrgControlId,
                        'compliance_id': compliance.ComplianceId,
                        'status': 'skipped',
                        'message': 'No organizational control content to audit'
                    })
                    continue
                
                # Build AI prompt for control mapping
                prompt = f"""
You are a GRC compliance expert. Analyze if the organizational control satisfies the framework compliance requirement.

**Framework Compliance Requirement:**
- Title: {compliance.ComplianceTitle}
- Description: {compliance.ComplianceItemDescription}
- Identifier: {compliance.Identifier}
- Criticality: {compliance.Criticality}
- Mandatory/Optional: {compliance.MandatoryOptional}

**Organizational Control in Place:**
{org_content[:5000]}

**Task:**
Determine if the organizational control FULLY MAPS, PARTIALLY MAPS, or DOES NOT MAP to the framework requirement.

Respond in this exact JSON format:
{{
    "mapping_status": "fully_mapped" | "partially_mapped" | "not_mapped",
    "confidence_score": <0-100>,
    "what_is_satisfying": "<what parts of the organizational control satisfy the requirement>",
    "what_is_left": "<what is missing or incomplete - leave empty if fully mapped>",
    "why_not_mapped": "<reason if not mapped - leave empty if fully or partially mapped>",
    "detailed_analysis": "<comprehensive analysis of the mapping>"
}}
"""
                
                # Call AI API
                ai_response = call_ai_api(
                    prompt, 
                    audit_id=org_control.OrgControlId, 
                    document_id=org_control.ComplianceId_id,
                    model_type='compliance'
                )
                
                # Parse AI response
                try:
                    # Clean response - remove markdown code blocks if present
                    clean_response = ai_response.strip()
                    if clean_response.startswith('```'):
                        clean_response = clean_response.split('\n', 1)[1]
                        clean_response = clean_response.rsplit('```', 1)[0]
                    
                    ai_result = json.loads(clean_response)
                    
                    # Update organizational control with AI results
                    org_control.MappingStatus = ai_result.get('mapping_status', 'not_audited')
                    org_control.ConfidenceScore = ai_result.get('confidence_score', 0)
                    org_control.AIAnalysis = ai_result  # All AI analysis data stored in JSON
                    org_control.LastAuditedAt = timezone.now()
                    org_control.save()
                    
                    results.append({
                        'org_control_id': org_control.OrgControlId,
                        'compliance_id': compliance.ComplianceId,
                        'compliance_title': compliance.ComplianceTitle,
                        'status': 'success',
                        'mapping_status': org_control.MappingStatus,
                        'confidence_score': org_control.ConfidenceScore
                    })
                    
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse AI response: {je}")
                    results.append({
                        'org_control_id': org_control.OrgControlId,
                        'compliance_id': compliance.ComplianceId,
                        'status': 'error',
                        'message': 'Failed to parse AI response'
                    })
                    
            except Compliance.DoesNotExist:
                results.append({
                    'org_control_id': org_control.OrgControlId,
                    'status': 'error',
                    'message': 'Compliance not found'
                })
            except Exception as e:
                logger.error(f"Error auditing org control {org_control.OrgControlId}: {e}")
                results.append({
                    'org_control_id': org_control.OrgControlId,
                    'status': 'error',
                    'message': str(e)
                })
        
        # Calculate summary
        success_count = sum(1 for r in results if r.get('status') == 'success')
        fully_mapped = sum(1 for r in results if r.get('mapping_status') == 'fully_mapped')
        partially_mapped = sum(1 for r in results if r.get('mapping_status') == 'partially_mapped')
        not_mapped = sum(1 for r in results if r.get('mapping_status') == 'not_mapped')
        
        return Response({
            'success': True,
            'message': f'Audit completed for {success_count} controls',
            'summary': {
                'total': len(results),
                'fully_mapped': fully_mapped,
                'partially_mapped': partially_mapped,
                'not_mapped': not_mapped,
                'errors': len(results) - success_count
            },
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error running control mapping audit: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== DELETE ORGANIZATIONAL CONTROL ====================
@csrf_exempt
@api_view(['DELETE'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def delete_organizational_control(request, org_control_id):
    """
    Delete an organizational control
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        org_control = OrganizationalControl.objects.get(OrgControlId=org_control_id)
        
        # Delete associated documents and files
        documents = OrganizationalControlDocument.objects.filter(OrgControlId_id=org_control_id)
        for doc in documents:
            if doc.DocumentPath:
                full_path = os.path.join(settings.MEDIA_ROOT, doc.DocumentPath)
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                    except Exception as e:
                        logger.warning(f"Could not delete file {full_path}: {e}")
            doc.delete()
        
        org_control.delete()
        
        return Response({
            'success': True,
            'message': 'Organizational control deleted successfully'
        })
        
    except OrganizationalControl.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Organizational control with ID {org_control_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error deleting organizational control: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== GET MAPPING STATISTICS ====================
@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_mapping_statistics(request, framework_id):
    """
    Get organizational control mapping statistics for dashboard
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        with connection.cursor() as cursor:
            # Check if organizational_controls table exists
            org_controls_exists = table_exists(cursor, 'organizational_controls')
            
            # Get total compliances in framework (from subpolicies under policies of this framework)
            cursor.execute("""
                SELECT COUNT(*) 
                FROM compliance c
                JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                JOIN policies p ON sp.PolicyId = p.PolicyId
                WHERE p.FrameworkId = %s
            """, [framework_id])
            total_compliances = cursor.fetchone()[0]
            
            if org_controls_exists:
                # Get mapping status counts from organizational_controls
                cursor.execute("""
                    SELECT 
                        oc.MappingStatus,
                        COUNT(*) as count
                    FROM organizational_controls oc
                    JOIN compliance c ON oc.ComplianceId = c.ComplianceId
                    JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                    JOIN policies p ON sp.PolicyId = p.PolicyId
                    WHERE p.FrameworkId = %s
                    GROUP BY oc.MappingStatus
                """, [framework_id])
                
                stats = {}
                for row in cursor.fetchall():
                    stats[row[0]] = row[1]
                
                # Get compliances with org controls
                cursor.execute("""
                    SELECT COUNT(DISTINCT oc.ComplianceId) 
                    FROM organizational_controls oc
                    JOIN compliance c ON oc.ComplianceId = c.ComplianceId
                    JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                    JOIN policies p ON sp.PolicyId = p.PolicyId
                    WHERE p.FrameworkId = %s
                """, [framework_id])
                with_org_controls = cursor.fetchone()[0]
            else:
                # No organizational_controls table - all controls are not audited
                stats = {}
                with_org_controls = 0
            
            # Calculate coverage
            total_mapped = stats.get('fully_mapped', 0) + stats.get('partially_mapped', 0)
            coverage_percentage = (total_mapped / total_compliances * 100) if total_compliances > 0 else 0
            
            return Response({
                'success': True,
                'statistics': {
                    'total_compliances': total_compliances,
                    'with_org_controls': with_org_controls,
                    'without_org_controls': total_compliances - with_org_controls,
                    'fully_mapped': stats.get('fully_mapped', 0),
                    'partially_mapped': stats.get('partially_mapped', 0),
                    'not_mapped': stats.get('not_mapped', 0),
                    'not_audited': total_compliances - with_org_controls,
                    'coverage_percentage': round(coverage_percentage, 2)
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting mapping statistics: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== GET ALL FRAMEWORKS WITH ORG CONTROL STATS ====================
@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_frameworks_with_org_stats(request):
    """
    Get all frameworks with their organizational control statistics
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    f.FrameworkId,
                    f.FrameworkName,
                    f.Identifier,
                    COUNT(DISTINCT c.ComplianceId) as total_compliances,
                    COUNT(DISTINCT oc.ComplianceId) as with_org_controls,
                    SUM(CASE WHEN oc.MappingStatus = 'fully_mapped' THEN 1 ELSE 0 END) as fully_mapped,
                    SUM(CASE WHEN oc.MappingStatus = 'partially_mapped' THEN 1 ELSE 0 END) as partially_mapped,
                    SUM(CASE WHEN oc.MappingStatus = 'not_mapped' THEN 1 ELSE 0 END) as not_mapped
                FROM frameworks f
                LEFT JOIN compliance c ON f.FrameworkId = c.FrameworkId
                LEFT JOIN organizational_controls oc ON c.ComplianceId = oc.ComplianceId
                GROUP BY f.FrameworkId, f.FrameworkName, f.Identifier
                ORDER BY f.FrameworkName
            """)
            
            frameworks = []
            for row in cursor.fetchall():
                total_compliances = row[3] or 0
                fully_mapped = row[5] or 0
                partially_mapped = row[6] or 0
                
                coverage = ((fully_mapped + partially_mapped) / total_compliances * 100) if total_compliances > 0 else 0
                
                frameworks.append({
                    'FrameworkId': row[0],
                    'FrameworkName': row[1],
                    'Identifier': row[2],
                    'total_compliances': total_compliances,
                    'with_org_controls': row[4] or 0,
                    'fully_mapped': fully_mapped,
                    'partially_mapped': partially_mapped,
                    'not_mapped': row[7] or 0,
                    'coverage_percentage': round(coverage, 2)
                })
            
            return Response({
                'success': True,
                'frameworks': frameworks
            })
            
    except Exception as e:
        logger.error(f"Error getting frameworks with org stats: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

