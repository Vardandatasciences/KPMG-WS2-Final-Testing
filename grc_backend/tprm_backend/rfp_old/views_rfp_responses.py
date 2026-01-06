import json
import uuid
import hashlib
import logging
import threading
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from .models import RFP, Vendor, VendorInvitation, RFPResponse, RFPUnmatchedVendor
from .rfp_authentication import JWTAuthentication, SimpleAuthenticatedPermission
from rbac.tprm_decorators import rbac_rfp_required, rbac_rfp_optional

# Import risk analysis service for automatic risk generation
logger = logging.getLogger(__name__)


def trigger_rfp_risk_analysis(rfp_response):
    """
    Trigger automatic risk analysis for RFP response submission
    This is called automatically when a vendor submits their proposal
    
    This function runs SYNCHRONOUSLY and should only be called from
    trigger_rfp_risk_analysis_async() for background execution
    """
    try:
        print(f"[RISK_ANALYSIS] Starting risk analysis for RFP Response {rfp_response.response_id}")
        logger.info(f"[RISK_ANALYSIS] Starting risk analysis for RFP Response {rfp_response.response_id}")
        
        # Import here to avoid circular dependencies
        from rfp_risk_analysis.entity_service import EntityDataService
        
        print(f"[RISK_ANALYSIS] EntityDataService imported successfully")
        
        # Initialize the entity data service
        entity_service = EntityDataService()
        
        print(f"[RISK_ANALYSIS] EntityDataService initialized, calling generate_risks_for_entity_data_row")
        print(f"[RISK_ANALYSIS] Parameters: entity='RFP', table='rfp_responses', row_id={rfp_response.response_id}")
        
        # Generate risks for this RFP response
        # entity='RFP', table='rfp_responses', row_id=response_id
        risks = entity_service.generate_risks_for_entity_data_row(
            entity='RFP',
            table_name='rfp_responses',
            row_id=str(rfp_response.response_id)
        )
        
        print(f"[RISK_ANALYSIS] Successfully generated {len(risks)} risks")
        logger.info(f"[RISK_ANALYSIS] Successfully generated {len(risks)} risks for RFP Response {rfp_response.response_id}")
        
        # Log each risk ID
        for risk in risks:
            print(f"[RISK_ANALYSIS] Created Risk: {risk.id} - {risk.title}")
            logger.info(f"[RISK_ANALYSIS] Created Risk: {risk.id} - {risk.title}")
        
        return {
            'success': True,
            'risks_generated': len(risks),
            'risk_ids': [risk.id for risk in risks]
        }
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"[RISK_ANALYSIS] ERROR triggering risk analysis for RFP Response {rfp_response.response_id}")
        print(f"[RISK_ANALYSIS] Error message: {str(e)}")
        print(f"[RISK_ANALYSIS] Full traceback:\n{error_traceback}")
        logger.error(f"[RISK_ANALYSIS] Error triggering risk analysis for RFP Response {rfp_response.response_id}: {e}")
        logger.error(f"[RISK_ANALYSIS] Full traceback:\n{error_traceback}")
        # Don't fail the response submission if risk analysis fails
        return {
            'success': False,
            'error': str(e),
            'traceback': error_traceback
        }


def trigger_rfp_risk_analysis_async(response_id):
    """
    Trigger risk analysis asynchronously in a background thread
    This prevents timeout errors during RFP response submission
    
    Args:
        response_id: The ID of the RFP response to analyze
    """
    try:
        print(f"[ASYNC] Starting background risk analysis for response {response_id}")
        logger.info(f"[ASYNC] Starting background risk analysis for response {response_id}")
        
        # Get the RFP response object
        from django.db import connection
        connection.close()  # Close connection before thread to avoid issues
        
        rfp_response = RFPResponse.objects.get(response_id=response_id)
        
        # Run risk analysis synchronously in this thread
        result = trigger_rfp_risk_analysis(rfp_response)
        
        if result['success']:
            print(f"[ASYNC] Background risk analysis completed: {result['risks_generated']} risks generated")
            logger.info(f"[ASYNC] Background risk analysis completed for response {response_id}: {result['risks_generated']} risks")
        else:
            print(f"[ASYNC] Background risk analysis failed: {result.get('error', 'Unknown error')}")
            logger.warning(f"[ASYNC] Background risk analysis failed for response {response_id}: {result.get('error')}")
            
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"[ASYNC] Exception in background risk analysis: {str(e)}")
        print(f"[ASYNC] Traceback:\n{error_traceback}")
        logger.error(f"[ASYNC] Background risk analysis exception for response {response_id}: {e}")
        logger.error(f"[ASYNC] Traceback:\n{error_traceback}")


def generate_invitation_id():
    """Generate a unique invitation ID"""
    return f"INV{uuid.uuid4().hex[:8].upper()}"


def build_dynamic_urls(base_url, utm_params=None, vendor_data=None, rfp_id=None):
    """
    Build dynamic URLs for invitation, acknowledgment, and submission
    """
    # Strictly use http://localhost:3000 for vendor access portal
    if not base_url or 'localhost' in base_url or '127.0.0.1' in base_url or 'ngrok' in base_url.lower():
        base_url = "http://localhost:3000/vendor-portal"
    
    # Start with base parameters
    base_params = ["submissionSource=open"]
    
    # Add RFP ID if provided
    if rfp_id:
        base_params.append(f"rfpId={rfp_id}")
    
    # Build UTM parameters
    if utm_params:
        for key, value in utm_params.items():
            if value:
                base_params.append(f"{key}={value}")
    
    # Build vendor data parameters
    if vendor_data:
        if vendor_data.get('vendorName'):
            base_params.append(f"vendorName={vendor_data['vendorName']}")
        if vendor_data.get('contactEmail'):
            base_params.append(f"contactEmail={vendor_data['contactEmail']}")
        if vendor_data.get('contactPhone'):
            base_params.append(f"contactPhone={vendor_data['contactPhone']}")
        if vendor_data.get('org'):
            base_params.append(f"org={vendor_data['org']}")
    
    # Build query string
    query_string = "&".join(base_params)
    
    # Build URLs
    invitation_url = f"{base_url}?{query_string}"
    acknowledgment_url = f"{base_url}?{query_string}&acknowledged=true"
    submission_url = f"{base_url}?{query_string}&submitted=true"
    
    return {
        'invitation_url': invitation_url,
        'acknowledgment_url': acknowledgment_url,
        'submission_url': submission_url
    }


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@rbac_rfp_optional('create_rfp')
def create_unmatched_vendor(request):
    """
    Create an unmatched vendor record for open RFP submissions
    """
    try:
        data = json.loads(request.body)
        
        # Required fields
        rfp_id = data.get('rfpId')
        vendor_name = data.get('vendorName', '')
        vendor_email = data.get('contactEmail', '')
        company_name = data.get('org', '')
        vendor_phone = data.get('contactPhone', '')
        
        # UTM parameters
        utm_params = data.get('utmParameters', {})
        
        # Additional submission data
        submission_data = data.get('submissionData', {})
        
        if not rfp_id or not vendor_name or not vendor_email:
            return JsonResponse({
                'success': False,
                'error': 'RFP ID, vendor name, and contact email are required'
            }, status=400)
        
        # Validate RFP exists
        try:
            rfp = RFP.objects.get(rfp_id=rfp_id)
        except RFP.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'RFP not found: {rfp_id}'
            }, status=404)
        
        with transaction.atomic():
            # Create unmatched vendor record
            unmatched_vendor = RFPUnmatchedVendor.objects.create(
                vendor_name=vendor_name,
                vendor_email=vendor_email,
                vendor_phone=vendor_phone,
                company_name=company_name,
                submission_data={
                    **submission_data,
                    'utm_parameters': utm_params,
                    'created_at': timezone.now().isoformat(),
                    'rfp_id': rfp_id,
                    'rfp_title': rfp.rfp_title,
                    'rfp_number': rfp.rfp_number
                },
                matching_status='unmatched'
            )
            
            # Build dynamic URLs
            vendor_data = {
                'vendorName': vendor_name,
                'contactEmail': vendor_email,
                'contactPhone': vendor_phone,
                'org': company_name
            }
            
            # Strictly use http://localhost:3000 for vendor access portal
            base_url_param = data.get('baseUrl', 'http://localhost:3000/vendor-portal')
            if 'localhost' in base_url_param or '127.0.0.1' in base_url_param or 'ngrok' in base_url_param.lower():
                base_url_param = 'http://localhost:3000/vendor-portal'
            urls = build_dynamic_urls(
                base_url=base_url_param,
                utm_params=utm_params,
                vendor_data=vendor_data,
                rfp_id=rfp_id
            )
            
            # Create invitation record linked to unmatched vendor
            invitation = VendorInvitation.objects.create(
                rfp=rfp,
                vendor=None,  # No matched vendor yet
                vendor_email=vendor_email,
                vendor_name=vendor_name,
                vendor_phone=vendor_phone,
                company_name=company_name,
                unique_token=generate_invitation_id(),
                invitation_status='OPENED',
                is_matched_vendor=False,
                submission_source='open',
                invitation_url=urls['invitation_url'],
                acknowledgment_url=urls['acknowledgment_url'],
                submission_url=urls['submission_url'],
                utm_parameters=utm_params
            )
            
            # Update unmatched vendor with invitation ID
            unmatched_vendor.invitation_id = invitation.invitation_id
            unmatched_vendor.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Unmatched vendor created successfully',
                'unmatched_vendor_id': unmatched_vendor.unmatched_id,
                'invitation_id': invitation.invitation_id,
                'unique_token': invitation.unique_token,
                'urls': urls
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Error in create_unmatched_vendor: {str(e)}")
        print(f"[ERROR] Traceback: {error_traceback}")
        return JsonResponse({
            'success': False,
            'error': f'Failed to create unmatched vendor: {str(e)}',
            'details': error_traceback
        }, status=500)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@rbac_rfp_optional('create_rfp_response')
def create_rfp_response(request):
    """
    Create a new RFP response from vendor portal
    Accepts JSON with invitationId, org, vendorName, contactEmail, contactPhone, proposalData
    """
    logger.info(f'[create_rfp_response] Request received - Method: {request.method}, Path: {request.path}')
    try:
        # Parse request data
        data = json.loads(request.body)
        logger.info(f'[create_rfp_response] Request data parsed - rfpId: {data.get("rfpId")}, vendorId: {data.get("vendorId")}, has_proposalData: {bool(data.get("proposalData"))}')
        
        # Basic info
        rfp_id = data.get('rfpId')
        vendor_id = data.get('vendorId')
        invitation_id = data.get('invitationId')  # For backward compatibility
        org = data.get('org', '')
        vendor_name = data.get('vendorName', '')
        contact_email = data.get('contactEmail', '')
        contact_phone = data.get('contactPhone', '')
        
        # Convert vendor_id to integer if it's a string
        if vendor_id and isinstance(vendor_id, str):
            try:
                vendor_id = int(vendor_id)
            except ValueError:
                vendor_id = None
        
        # CRITICAL: vendor_id should come from invitation, but for open RFPs it may come from request
        # We'll validate this after finding the invitation
        
        # Documents
        response_documents = data.get('responseDocuments', {})
        document_urls = data.get('documentUrls', {})

        print(f"[CREATE_RFP_RESPONSE] Received documentUrls: {json.dumps(document_urls, indent=2)}")
        print(f"[CREATE_RFP_RESPONSE] documentUrls type: {type(document_urls)}, count: {len(document_urls) if isinstance(document_urls, dict) else 0}")
        
        # Log the complete response_documents structure
        logger.info(f'[create_rfp_response] Response documents received - type: {type(response_documents)}, keys: {list(response_documents.keys()) if isinstance(response_documents, dict) else "N/A"}')
        logger.debug(f'[create_rfp_response] Response documents structure: {response_documents}')
        
        # Proposal data
        proposal_data = data.get('proposalData', {})
        logger.info(f'[create_rfp_response] Proposal data received - has_dynamicFields: {bool(proposal_data.get("dynamicFields"))}, dynamicFields_keys: {list(proposal_data.get("dynamicFields", {}).keys()) if proposal_data.get("dynamicFields") else []}')
        if proposal_data.get('dynamicFields'):
            logger.debug(f'[create_rfp_response] Dynamic fields content: {proposal_data.get("dynamicFields")}')
        
        # Ensure response_documents contains all data in nested format
        # Priority: Use responseDocuments from request if it has the complete structure
        # Otherwise, build it from proposal_data
        if not response_documents or not isinstance(response_documents, dict):
            logger.info('[create_rfp_response] response_documents is empty, building from proposal_data')
            response_documents = {}
        
        # Check if response_documents has the complete nested structure
        has_complete_structure = (
            isinstance(response_documents, dict) and
            ('companyInfo' in response_documents or 'financialInfo' in response_documents or 
             'rfpResponses' in response_documents or 'dynamicFields' in response_documents)
        )
        
        if not has_complete_structure and proposal_data and isinstance(proposal_data, dict):
            logger.info('[create_rfp_response] Building complete nested structure from proposal_data')
            # Build complete structure from proposal_data
            if proposal_data.get('companyInfo'):
                response_documents['companyInfo'] = proposal_data.get('companyInfo')
            
            if proposal_data.get('financialInfo'):
                response_documents['financialInfo'] = proposal_data.get('financialInfo')
            
            if proposal_data.get('responses'):
                response_documents['rfpResponses'] = proposal_data.get('responses')
            
            if proposal_data.get('keyPersonnel'):
                response_documents['teamInfo'] = {
                    'keyPersonnel': proposal_data.get('keyPersonnel')
                }
            
            if proposal_data.get('dynamicFields'):
                response_documents['dynamicFields'] = proposal_data.get('dynamicFields')
                logger.info(f'[create_rfp_response] Added dynamicFields to response_documents: {list(proposal_data.get("dynamicFields", {}).keys())}')
            
            if proposal_data.get('documents'):
                response_documents['uploadedDocuments'] = proposal_data.get('documents')
        
        # Ensure vendor contact info is in companyInfo (merge if needed)
        if 'companyInfo' not in response_documents:
            response_documents['companyInfo'] = {}
        
        if not response_documents['companyInfo'].get('vendor_name') and vendor_name:
            response_documents['companyInfo']['vendor_name'] = vendor_name
        if not response_documents['companyInfo'].get('contact_email') and contact_email:
            response_documents['companyInfo']['contact_email'] = contact_email
        if not response_documents['companyInfo'].get('contact_phone') and contact_phone:
            response_documents['companyInfo']['contact_phone'] = contact_phone
        if not response_documents['companyInfo'].get('org') and org:
            response_documents['companyInfo']['org'] = org
        
        logger.info(f'[create_rfp_response] Final response_documents structure - keys: {list(response_documents.keys())}, has_dynamicFields: {"dynamicFields" in response_documents}')
        if 'dynamicFields' in response_documents:
            logger.debug(f'[create_rfp_response] Dynamic fields in response_documents: {list(response_documents["dynamicFields"].keys()) if isinstance(response_documents["dynamicFields"], dict) else "N/A"}')
        
        # Extract proposed value from proposal data
        proposed_value = None
        if proposal_data and isinstance(proposal_data, dict):
            company_info = proposal_data.get('companyInfo', {})
            if company_info and isinstance(company_info, dict):
                proposed_value = company_info.get('proposedValue')
                if proposed_value:
                    try:
                        proposed_value = float(proposed_value)
                    except (ValueError, TypeError):
                        proposed_value = None
        
        # Submission details
        submission_source = data.get('submissionSource', 'invited')
        completion_percentage = data.get('completionPercentage', 0)
        submitted_by = data.get('submittedBy', vendor_name)
        
        # UTM parameters for open submissions
        utm_params = data.get('utmParameters', {})
        
        # CRITICAL: Invitations must already exist - they are created during vendor selection, NOT here
        # If invitation_id is missing, attempt to locate the existing invitation using rfpId + vendorId
        if not invitation_id:
            if vendor_id:
                try:
                    invitation_lookup = VendorInvitation.objects.select_related('vendor').filter(
                        rfp_id=rfp_id,
                        vendor_id=vendor_id
                    ).order_by('-invited_date').first()
                    if invitation_lookup:
                        invitation_id = invitation_lookup.invitation_id
                        print(f"[RECOVERY] Located invitation {invitation_id} using rfp_id={rfp_id} & vendor_id={vendor_id}")
                    else:
                        return JsonResponse({
                            'success': False,
                            'error': 'Invitation ID is required. No invitation found for the provided vendor. Please ensure the vendor was invited before submitting a response.'
                        }, status=400)
                except Exception as lookup_error:
                    print(f"[ERROR] Failed to locate invitation by vendor_id: {lookup_error}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Unable to locate invitation for this vendor. Please ensure the vendor was invited before submitting a response.'
                    }, status=400)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invitation ID is required. Invitations must be created during vendor selection, not during response submission.'
                }, status=400)
        
        # Convert completion_percentage to proper decimal or None
        if completion_percentage is not None:
            try:
                completion_percentage = float(completion_percentage)
            except (ValueError, TypeError):
                completion_percentage = None
        else:
            completion_percentage = None
        
        # Validate required fields
        if not vendor_name or not contact_email:
            return JsonResponse({
                'success': False,
                'error': 'Vendor name and contact email are required'
            }, status=400)
        
        # Get client information
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        with transaction.atomic():
            # CRITICAL: Invitations must already exist - they are created during vendor selection, NOT here
            invitation = None
            rfp = None
            unmatched_vendor = None
            
            # Get RFP
            if rfp_id:
                # New format: use rfpId directly
                from rfp.models import RFP
                try:
                    rfp = RFP.objects.get(rfp_id=rfp_id)
                except RFP.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': f'RFP not found: {rfp_id}'
                    }, status=404)
                
                # CRITICAL: Find invitation ONLY by invitation_id - no fallbacks
                # Invitations are created during vendor selection, not here
                if invitation_id:
                    try:
                        # Try to find by unique_token first (for string tokens like INV12345)
                        invitation = VendorInvitation.objects.select_related('vendor').get(unique_token=invitation_id)
                        print(f"[SUCCESS] Found invitation by unique_token: {invitation_id}, invitation_id={invitation.invitation_id}")
                    except VendorInvitation.DoesNotExist:
                        try:
                            # Try to find by numeric invitation_id
                            numeric_id = int(invitation_id)
                            invitation = VendorInvitation.objects.select_related('vendor').get(invitation_id=numeric_id)
                            print(f"[SUCCESS] Found invitation by numeric ID: {numeric_id}, invitation_id={invitation.invitation_id}")
                        except (ValueError, VendorInvitation.DoesNotExist):
                            return JsonResponse({
                                'success': False,
                                'error': f'Invitation not found: {invitation_id}. Invitations must be created during vendor selection.'
                            }, status=404)
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invitation ID is required. Invitations must be created during vendor selection.'
                    }, status=400)
                
                # CRITICAL: vendor_id comes from invitation table OR from request (for open RFPs)
                if invitation:
                    # Get vendor_id from invitation if it has a matched vendor
                    if invitation.vendor:
                        vendor_id = invitation.vendor.vendor_id
                        print(f"[CRITICAL] Using vendor_id from invitation.vendor: {vendor_id}")
                    else:
                        # For open RFPs, invitation.vendor might be NULL
                        # Use vendor_id from request if provided (it should match the invitation)
                        if vendor_id:
                            print(f"[CRITICAL] Invitation has no matched vendor, using vendor_id from request: {vendor_id}")
                        else:
                            return JsonResponse({
                                'success': False,
                                'error': 'Invitation does not have a matched vendor and no vendorId provided in request. Please provide vendorId for open RFP submissions.'
                            }, status=400)
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invitation not found. Invitations must be created during vendor selection.'
                    }, status=404)
                
                # Update invitation status if found
                if invitation:
                    invitation.invitation_status = 'SUBMITTED'
                    invitation.save()
                    print(f"[SUCCESS] Updated invitation status to SUBMITTED: {invitation.invitation_id}")
                    print(f"[CRITICAL] invitation.invitation_id={invitation.invitation_id}, extracted vendor_id={vendor_id}")
                else:
                    print(f"[WARN] No invitation found for rfp_id: {rfp_id}, vendor_id: {vendor_id}, invitation_id: {invitation_id}")
                    print(f"[WARN] Attempted to find by: invitation_id={invitation_id}, vendor_id={vendor_id}, email={contact_email}")
                        
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'RFP ID is required'
                }, status=400)
            
            # Check if response already exists
            # CRITICAL: Use select_for_update to prevent race conditions and duplicate entries
            existing_response = None
            if rfp:
                # Only check for existing responses for invited submissions
                # Build filter conditions
                filter_conditions = {'rfp': rfp}
                
                # Add vendor_id if available
                if vendor_id:
                    filter_conditions['vendor_id'] = vendor_id
                
                # Add invitation_id if we found one
                if invitation:
                    filter_conditions['invitation_id'] = invitation.invitation_id
                
                # CRITICAL: Use select_for_update to lock the row and prevent race conditions
                # This ensures only one submission can create/update at a time
                try:
                    existing_response = RFPResponse.objects.select_for_update(nowait=True).filter(**filter_conditions).first()
                    if existing_response:
                        print(f"[SUCCESS] Found existing response (locked): {existing_response.response_id}")
                    else:
                        print(f"[INFO] No existing response found, will create new one")
                except Exception as lock_error:
                    # If lock fails (another transaction has it), wait and retry
                    print(f"[WARN] Lock conflict, retrying: {lock_error}")
                    import time
                    time.sleep(0.1)  # Brief wait
                    existing_response = RFPResponse.objects.filter(**filter_conditions).first()
                    if existing_response:
                        print(f"[SUCCESS] Found existing response (after retry): {existing_response.response_id}")
            # Extract proposed value from proposal data
            proposed_value = None
            if proposal_data and isinstance(proposal_data, dict):
                company_info = proposal_data.get('companyInfo', {})
                if company_info and isinstance(company_info, dict):
                    proposed_value = company_info.get('proposedValue')
                    if proposed_value:
                        try:
                            proposed_value = float(proposed_value)
                        except (ValueError, TypeError):
                            proposed_value = None
            
            if existing_response:
                # Update existing response
                current_time = timezone.now()
                
                # CRITICAL: ALWAYS set invitation_id if we found one
                if invitation:
                    existing_response.invitation_id = invitation.invitation_id
                    print(f"[CRITICAL] Set invitation_id={invitation.invitation_id} for existing response: {existing_response.response_id}")
                else:
                    print(f"[WARN] No invitation found when updating existing response {existing_response.response_id}")
                
                # CRITICAL: ALWAYS set vendor_id - use invitation vendor_id if available
                final_vendor_id = vendor_id
                if invitation:
                    if invitation.vendor:
                        final_vendor_id = invitation.vendor.vendor_id
                        print(f"[CRITICAL] Using vendor_id from invitation.vendor: {final_vendor_id}")
                    elif hasattr(invitation, 'unmatched_vendor_id') and invitation.unmatched_vendor_id:
                        final_vendor_id = invitation.unmatched_vendor_id
                        print(f"[CRITICAL] Using unmatched_vendor_id from invitation: {final_vendor_id}")
                
                if final_vendor_id:
                    existing_response.vendor_id = final_vendor_id
                    print(f"[CRITICAL] Set vendor_id={final_vendor_id} for existing response: {existing_response.response_id}")
                else:
                    print(f"[WARN] No vendor_id available when updating existing response {existing_response.response_id}")
                
                # Update all fields - using fields that exist in the database
                # Note: vendor_name, contact_email, contact_phone are not in the database schema
                # We'll store this information in the proposal_data JSON field
                
                # Update response_documents with complete nested structure
                # Save all form fields (static + dynamic) in response_documents JSON
                logger.info(f'[create_rfp_response] Updating existing response - response_id: {existing_response.response_id}')
                logger.debug(f'[create_rfp_response] Current response_documents: {existing_response.response_documents}')
                logger.debug(f'[create_rfp_response] New response_documents: {response_documents}')
                
                # Use the complete response_documents structure from request
                # This contains all nested data: companyInfo, financialInfo, rfpResponses, teamInfo, compliance, dynamicFields, etc.
                existing_response.response_documents = response_documents
                
                # Submission details
                existing_response.submission_source = submission_source
                existing_response.submitted_by = submitted_by
                
                # Documents
                existing_response.document_urls = document_urls
                
                # Proposal data
                existing_response.proposal_data = proposal_data
                existing_response.draft_data = proposal_data
                
                # CRITICAL: Store UTM parameters in external_submission_data
                if utm_params:
                    existing_response.external_submission_data = {
                        'utm_parameters': utm_params,
                        'submission_source': submission_source,
                        'ip_address': ip_address if ip_address else None,
                        'user_agent': user_agent if user_agent else None,
                        'submission_timestamp': current_time.isoformat()
                    }
                    print(f"[CRITICAL] Stored UTM parameters in external_submission_data: {utm_params}")
                else:
                    existing_response.external_submission_data = {
                        'submission_source': submission_source,
                        'ip_address': ip_address if ip_address else None,
                        'user_agent': user_agent if user_agent else None,
                        'submission_timestamp': current_time.isoformat()
                    }
                
                # Financial info
                if proposed_value is not None:
                    existing_response.proposed_value = proposed_value
                existing_response.technical_score = None
                existing_response.commercial_score = None
                existing_response.overall_score = None
                existing_response.weighted_final_score = None
                
                # Evaluation
                existing_response.evaluation_status = 'SUBMITTED'
                existing_response.auto_rejected = False
                existing_response.rejection_reason = None
                existing_response.evaluated_by = None
                existing_response.evaluation_date = None
                existing_response.evaluation_comments = None
                
                # Progress
                existing_response.completion_percentage = completion_percentage
                existing_response.last_saved_at = current_time
                
                # FINAL SAFETY CHECK: Ensure IDs are saved
                if invitation and existing_response.invitation_id != invitation.invitation_id:
                    existing_response.invitation_id = invitation.invitation_id
                    print(f"[FINAL SAFETY] Force updating invitation_id to {invitation.invitation_id}")
                
                # Determine final vendor_id for safety check
                final_vendor_id_safety = final_vendor_id
                if invitation:
                    if invitation.vendor:
                        final_vendor_id_safety = invitation.vendor.vendor_id
                    elif hasattr(invitation, 'unmatched_vendor_id') and invitation.unmatched_vendor_id:
                        final_vendor_id_safety = invitation.unmatched_vendor_id
                
                if final_vendor_id_safety and existing_response.vendor_id != final_vendor_id_safety:
                    existing_response.vendor_id = final_vendor_id_safety
                    print(f"[FINAL SAFETY] Force updating vendor_id to {final_vendor_id_safety}")
                
                existing_response.save()
                print(f"[FINAL SAFETY] Saved IDs to existing response {existing_response.response_id}: vendor_id={existing_response.vendor_id}, invitation_id={existing_response.invitation_id}")
                rfp_response = existing_response
            else:
                # CRITICAL: vendor_id comes from invitation or request
                # For open RFPs, invitation.vendor might be NULL, so we use vendor_id from request
                if not vendor_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Vendor ID is required. Must be provided in request or come from invitation.'
                    }, status=400)
                
                vendor_id_to_use = vendor_id
                
                # Get document info from request data
                response_documents = data.get('responseDocuments', {})
                document_urls = data.get('documentUrls', {})

                # Create new response with all fields
                current_time = timezone.now()
                
                # IMPORTANT: Check one more time if response exists to avoid duplicate key error
                # This handles race conditions and edge cases
                # CRITICAL: Use select_for_update to prevent race conditions
                final_check_response = None
                if vendor_id_to_use:
                    try:
                        final_check_response = RFPResponse.objects.select_for_update(nowait=True).filter(
                            rfp=rfp,
                            vendor_id=vendor_id_to_use
                        ).first()
                    except Exception:
                        # If lock fails, try without lock (another transaction might be creating it)
                        final_check_response = RFPResponse.objects.filter(
                            rfp=rfp,
                            vendor_id=vendor_id_to_use
                        ).first()
                
                if final_check_response:
                    # Update the existing response
                    print(f"[FINAL CHECK] Found existing response {final_check_response.response_id}, updating instead of creating")
                    
                    # CRITICAL: ALWAYS set invitation_id if we found one
                    if invitation:
                        final_check_response.invitation_id = invitation.invitation_id
                        print(f"[CRITICAL] Set invitation_id={invitation.invitation_id} for final check response: {final_check_response.response_id}")
                        
                        # Override vendor_id with invitation vendor if available
                        if invitation.vendor:
                            vendor_id_to_use = invitation.vendor.vendor_id
                            print(f"[CRITICAL] Overriding vendor_id with invitation.vendor.vendor_id: {vendor_id_to_use}")
                        elif hasattr(invitation, 'unmatched_vendor_id') and invitation.unmatched_vendor_id:
                            vendor_id_to_use = invitation.unmatched_vendor_id
                            print(f"[CRITICAL] Overriding vendor_id with invitation.unmatched_vendor_id: {vendor_id_to_use}")
                    
                    # CRITICAL: vendor_id MUST come from invitation - no fallbacks
                    if vendor_id_to_use:
                        final_check_response.vendor_id = vendor_id_to_use
                        print(f"[CRITICAL] Set vendor_id={vendor_id_to_use} for final check response: {final_check_response.response_id}")
                    else:
                        print(f"[WARN] No vendor_id available for final check response {final_check_response.response_id}")
                    # Use complete response_documents structure
                    logger.info(f'[create_rfp_response] Updating final check response with complete response_documents')
                    logger.debug(f'[create_rfp_response] Response documents: {response_documents}')
                    final_check_response.response_documents = response_documents
                    final_check_response.submission_source = submission_source
                    final_check_response.submitted_by = vendor_name
# Merge document_urls instead of overwriting - preserve existing documents
                    existing_doc_urls = final_check_response.document_urls or {}
                    if isinstance(existing_doc_urls, str):
                        try:
                            existing_doc_urls = json.loads(existing_doc_urls)
                        except json.JSONDecodeError:
                            existing_doc_urls = {}
                    if isinstance(document_urls, dict) and document_urls:
                        # Merge new document URLs with existing ones
                        merged_doc_urls = {**existing_doc_urls, **document_urls}
                        final_check_response.document_urls = merged_doc_urls
                        print(f"[FINAL CHECK] Merged document_urls: {len(merged_doc_urls)} documents")
                    elif existing_doc_urls:
                        # Keep existing if new ones are empty
                        final_check_response.document_urls = existing_doc_urls
                        print(f"[FINAL CHECK] Keeping existing document_urls: {len(existing_doc_urls)} documents")
                    else:
                        final_check_response.document_urls = document_urls or {}
                        print(f"[FINAL CHECK] Setting new document_urls: {len(document_urls or {})} documents")
                   
 
                    final_check_response.draft_data = proposal_data
                    final_check_response.proposed_value = proposed_value
                    final_check_response.evaluation_status = 'SUBMITTED'
                    final_check_response.completion_percentage = completion_percentage
                    final_check_response.last_saved_at = current_time
                    final_check_response.submission_date = current_time
                    
                    # CRITICAL: Store UTM parameters in external_submission_data
                    if utm_params:
                        final_check_response.external_submission_data = {
                            'utm_parameters': utm_params,
                            'submission_source': submission_source,
                            'ip_address': ip_address if ip_address else None,
                            'user_agent': user_agent if user_agent else None,
                            'submission_timestamp': current_time.isoformat()
                        }
                        print(f"[CRITICAL] Stored UTM parameters in final check response: {utm_params}")
                    
                    final_check_response.save()
                    
                    rfp_response = final_check_response
                    print(f"Updated existing response {final_check_response.response_id} for RFP {rfp.rfp_id} and vendor {vendor_id_to_use}")
                else:
                    # Create new response - guaranteed no duplicate
                    # CRITICAL: Determine final vendor_id and invitation_id
                    final_invitation_id = None
                    final_vendor_id_for_create = vendor_id_to_use
                    
                    if invitation:
                        final_invitation_id = invitation.invitation_id
                        print(f"[CRITICAL] Creating response with invitation_id={final_invitation_id}")
                        
                        # Override vendor_id with invitation vendor if available
                        if invitation.vendor:
                            final_vendor_id_for_create = invitation.vendor.vendor_id
                            print(f"[CRITICAL] Overriding vendor_id with invitation.vendor.vendor_id: {final_vendor_id_for_create}")
                        elif hasattr(invitation, 'unmatched_vendor_id') and invitation.unmatched_vendor_id:
                            final_vendor_id_for_create = invitation.unmatched_vendor_id
                            print(f"[CRITICAL] Overriding vendor_id with invitation.unmatched_vendor_id: {final_vendor_id_for_create}")
                    else:
                        print(f"[WARN] Creating response WITHOUT invitation_id")
                    
                    # CRITICAL: vendor_id MUST come from invitation - no fallbacks
                    if not final_vendor_id_for_create:
                        return JsonResponse({
                            'success': False,
                            'error': 'Vendor ID must come from invitation. Cannot create response without valid vendor_id from invitation.'
                        }, status=400)
                    
                    # CRITICAL: Final check right before creating to prevent duplicates
                    # This handles race conditions where multiple requests pass the initial check
                    final_duplicate_check = None
                    if final_vendor_id_for_create:
                        try:
                            final_duplicate_check = RFPResponse.objects.select_for_update(nowait=True).filter(
                                rfp=rfp,
                                vendor_id=final_vendor_id_for_create
                            ).first()
                        except Exception:
                            # If lock fails, check without lock
                            final_duplicate_check = RFPResponse.objects.filter(
                                rfp=rfp,
                                vendor_id=final_vendor_id_for_create
                            ).first()
                    
                    if final_duplicate_check:
                        # Another request created it, update instead
                        print(f"[DUPLICATE PREVENTION] Found response created by another request: {final_duplicate_check.response_id}, updating instead")
                        final_duplicate_check.response_documents = response_documents
                        final_duplicate_check.submission_source = submission_source
                        final_duplicate_check.submitted_by = vendor_name
                        final_duplicate_check.document_urls = document_urls if isinstance(document_urls, dict) else {}
                        final_duplicate_check.draft_data = proposal_data
                        final_duplicate_check.proposed_value = proposed_value
                        final_duplicate_check.evaluation_status = 'SUBMITTED'
                        final_duplicate_check.completion_percentage = completion_percentage
                        final_duplicate_check.last_saved_at = current_time
                        final_duplicate_check.submission_date = current_time
                        if invitation:
                            final_duplicate_check.invitation_id = invitation.invitation_id
                        if final_vendor_id_for_create:
                            final_duplicate_check.vendor_id = final_vendor_id_for_create
                        if utm_params:
                            final_duplicate_check.external_submission_data = {
                                'utm_parameters': utm_params,
                                'submission_source': submission_source,
                                'ip_address': ip_address if ip_address else None,
                                'user_agent': user_agent if user_agent else None,
                                'submission_timestamp': current_time.isoformat()
                            }
                        final_duplicate_check.save()
                        rfp_response = final_duplicate_check
                        print(f"[DUPLICATE PREVENTION] Updated existing response instead of creating duplicate: {rfp_response.response_id}")
                    else:
                        print(f"[CREATE] Creating new response for RFP {rfp.rfp_id}, vendor_id={final_vendor_id_for_create}, invitation_id={final_invitation_id}")
                        logger.info(f'[create_rfp_response] Creating new response - rfp_id: {rfp.rfp_id}, vendor_id: {final_vendor_id_for_create}, invitation_id: {final_invitation_id}')
                        logger.debug(f'[create_rfp_response] Response documents to save: {response_documents}')
                        
                        rfp_response = RFPResponse.objects.create(
                        # Basic info - CRITICAL: Always set both IDs
                        invitation_id=final_invitation_id,
                        rfp=rfp,
                        vendor_id=final_vendor_id_for_create,
                        
                        # Store complete nested structure in response_documents
                        # This contains all form fields: companyInfo, financialInfo, rfpResponses, teamInfo, compliance, dynamicFields, etc.
                        response_documents=response_documents,
                        
                        # Submission details
                        submission_source=submission_source,
                        submitted_by=vendor_name,
                        
                        # Documents
                        document_urls=document_urls if isinstance(document_urls, dict) else {},

                        
                        # Draft data
                        draft_data=proposal_data,  # Store initial submission as draft
                        
                        # CRITICAL: Store UTM parameters in external_submission_data
                        external_submission_data={
                            'utm_parameters': utm_params if utm_params else {},
                            'submission_source': submission_source,
                            'ip_address': ip_address if ip_address else None,
                            'user_agent': user_agent if user_agent else None,
                            'submission_timestamp': current_time.isoformat()
                        } if utm_params else {
                            'submission_source': submission_source,
                            'ip_address': ip_address if ip_address else None,
                            'user_agent': user_agent if user_agent else None,
                            'submission_timestamp': current_time.isoformat()
                        },
                        
                        # Financial info
                        proposed_value=proposed_value,
                        technical_score=None,
                        commercial_score=None,
                        overall_score=None,
                        weighted_final_score=None,
                        
                        # Evaluation
                        evaluation_status='SUBMITTED',
                        auto_rejected=False,
                        rejection_reason=None,
                        evaluated_by=None,
                        evaluation_date=None,
                        evaluation_comments=None,
                        
                        # Progress
                        completion_percentage=completion_percentage,
                        last_saved_at=current_time
                    )
                    print(f"Created new response {rfp_response.response_id} for RFP {rfp.rfp_id}, vendor_id={final_vendor_id_for_create}, invitation_id={final_invitation_id}")
                    
                    # FINAL SAFETY CHECK: Ensure IDs are saved even if something went wrong
                    needs_update = False
                    if invitation and rfp_response.invitation_id != invitation.invitation_id:
                        rfp_response.invitation_id = invitation.invitation_id
                        needs_update = True
                        print(f"[FINAL SAFETY] Updating invitation_id to {invitation.invitation_id}")
                    
                    # Determine final vendor_id
                    final_vendor_id_check = final_vendor_id_for_create
                    if invitation:
                        if invitation.vendor:
                            final_vendor_id_check = invitation.vendor.vendor_id
                        elif hasattr(invitation, 'unmatched_vendor_id') and invitation.unmatched_vendor_id:
                            final_vendor_id_check = invitation.unmatched_vendor_id
                    
                    if final_vendor_id_check and rfp_response.vendor_id != final_vendor_id_check:
                        rfp_response.vendor_id = final_vendor_id_check
                        needs_update = True
                        print(f"[FINAL SAFETY] Updating vendor_id to {final_vendor_id_check}")
                    
                    if needs_update:
                        rfp_response.save()
                        print(f"[FINAL SAFETY] Saved IDs to response {rfp_response.response_id}: vendor_id={rfp_response.vendor_id}, invitation_id={rfp_response.invitation_id}")
                
                # Invitation status was already updated earlier
            
            # Prepare response data
            response_data = {
                'success': True,
                'message': 'RFP response submitted successfully',
                'response_id': rfp_response.response_id,
                'submission_date': rfp_response.submission_date.isoformat() if rfp_response.submission_date else timezone.now().isoformat(),
                'submitted_at': rfp_response.submission_date.isoformat() if rfp_response.submission_date else timezone.now().isoformat(),  # For frontend compatibility
                'rfp_title': rfp.rfp_title if rfp else None,
                'rfp_number': rfp.rfp_number if rfp else None,
                'vendor_name': vendor_name,
                'contact_email': contact_email,
                'org': org,  # Add org field to response
                'completion_percentage': float(completion_percentage) if completion_percentage else 0
            }
            
            # Add unmatched vendor information if applicable
            if unmatched_vendor:
                response_data.update({
                    'unmatched_vendor_id': unmatched_vendor.unmatched_id,
                    'invitation_id': invitation.invitation_id if invitation else None,
                    'unique_token': invitation.unique_token if invitation else None,
                    'submission_source': 'open',
                    'is_matched_vendor': False
                })
        
        # ===================================================================
        # AUTOMATIC RISK GENERATION - ASYNC BACKGROUND PROCESSING
        # ===================================================================
        # Trigger risk analysis ASYNCHRONOUSLY in a background thread
        # This prevents timeout errors and allows instant response to user
        # IMPORTANT: This must be AFTER the transaction commits to ensure
        # the RFP response is fully saved and accessible
        if 'rfp_response' in locals() and rfp_response and hasattr(rfp_response, 'response_id'):
            response_id = rfp_response.response_id
            print(f"[SUBMISSION] Queuing background risk analysis for response {response_id}")
            logger.info(f"[SUBMISSION] Queuing background risk analysis for response {response_id}")
            
            try:
                # Start risk analysis in a background thread (non-blocking)
                analysis_thread = threading.Thread(
                    target=trigger_rfp_risk_analysis_async,
                    args=(response_id,),
                    daemon=True,
                    name=f"RiskAnalysis-{response_id}"
                )
                analysis_thread.start()
                
                print(f"[SUBMISSION] Background risk analysis thread started for response {response_id}")
                logger.info(f"[SUBMISSION] Background risk analysis thread started successfully for response {response_id}")
                
            except Exception as e:
                # If thread creation fails, log but don't fail the submission
                import traceback
                error_traceback = traceback.format_exc()
                print(f"[SUBMISSION] Failed to start background risk analysis thread: {str(e)}")
                print(f"[SUBMISSION] Traceback:\n{error_traceback}")
                logger.error(f"Failed to start background risk analysis thread for response {response_id}: {e}")
                logger.error(f"Traceback:\n{error_traceback}")
        else:
            print(f"[SUBMISSION] WARNING: Cannot trigger risk analysis - rfp_response not properly initialized")
            logger.warning(f"[SUBMISSION] Cannot trigger risk analysis - rfp_response not properly initialized")
        
        return JsonResponse(response_data)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Error in create_rfp_response: {str(e)}")
        print(f"[ERROR] Traceback: {error_traceback}")
        return JsonResponse({
            'success': False,
            'error': f'Failed to submit RFP response: {str(e)}',
            'details': error_traceback
        }, status=500)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@rbac_rfp_optional('create_rfp_response')
def upload_response_asset(request):
    """
    Upload an attachment for the rich text RFP response editor.
    Stores the file in S3 (via the microservice) and records metadata in s3_files.
    Optionally updates the corresponding RFP response document attachments.
    """
    try:
        file = request.FILES.get('file')
        criteria_id = request.POST.get('criteriaId')
        rfp_id = request.POST.get('rfpId')
        vendor_id = request.POST.get('vendorId')
        invitation_id = request.POST.get('invitationId')
        response_id = request.POST.get('responseId')
        uploaded_by = request.POST.get('uploadedBy')
 
        if not file or not criteria_id or not rfp_id:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: file, criteriaId, rfpId'
            }, status=400)
 
        try:
            rfp_id_int = int(rfp_id)
        except (TypeError, ValueError):
            return JsonResponse({
                'success': False,
                'error': 'Invalid rfpId provided'
            }, status=400)
 
        vendor_id_int = None
        if vendor_id:
            try:
                vendor_id_int = int(vendor_id)
            except (TypeError, ValueError):
                vendor_id_int = None
 
        response_id_int = None
        if response_id:
            try:
                response_id_int = int(response_id)
            except (TypeError, ValueError):
                response_id_int = None
 
        # Enforce 50MB size limit (consistent with other uploads)
        max_size = 50 * 1024 * 1024
        if file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': 'File size exceeds 50MB limit'
            }, status=400)
 
        import os
        import uuid
        import tempfile
 
        file_extension = os.path.splitext(file.name)[1] or ''
        safe_criteria = str(criteria_id).replace('/', '_')
        unique_filename = f"rfp_response_{rfp_id}_{safe_criteria}_{uuid.uuid4().hex}{file_extension}"
 
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            file.seek(0)
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
 
        try:
            from rfp.s3_service import get_s3_service
            s3_service = get_s3_service()
            user_identifier = str(
                vendor_id_int
                or invitation_id
                or uploaded_by
                or 'vendor_portal'
            )
 
            metadata = {
                'context': 'rfp_response_attachment',
                'criteria_id': str(criteria_id),
                'response_id': response_id_int,
                'invitation_id': invitation_id,
                'vendor_id': vendor_id_int,
                'original_filename': file.name,
                'content_type': file.content_type
            }
 
            upload_result = s3_service.upload_file(
                file_path=temp_file_path,
                user_id=user_identifier,
                custom_file_name=unique_filename,
                rfp_id=rfp_id_int,
                metadata=metadata
            )
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
 
        if not upload_result.get('success'):
            return JsonResponse({
                'success': False,
                'error': f"S3 upload failed: {upload_result.get('error', 'Unknown error')}"
            }, status=500)
 
        attachment_payload = {
            'id': upload_result.get('s3_file_id'),
            'url': upload_result.get('s3_url'),
            'key': upload_result.get('s3_key'),
            'fileName': upload_result.get('stored_name') or unique_filename,
            'storedName': upload_result.get('stored_name') or unique_filename,
            'originalFilename': file.name,
            'fileSize': upload_result.get('file_size') or file.size,
            'contentType': file.content_type,
            'criteriaId': str(criteria_id),
            'uploadedAt': timezone.now().isoformat(),
            'isImage': file.content_type.startswith('image/')
        }
 
        # Attempt to update the response record if we can resolve it
        response_record = None
        if response_id_int:
            response_record = RFPResponse.objects.filter(response_id=response_id_int).first()
        elif vendor_id_int:
            response_record = RFPResponse.objects.filter(rfp_id=rfp_id_int, vendor_id=vendor_id_int).first()
        elif invitation_id:
            response_record = RFPResponse.objects.filter(rfp_id=rfp_id_int, invitation_id=invitation_id).first()
 
        if response_record:
            response_docs = response_record.response_documents or {}
            if isinstance(response_docs, str):
                try:
                    response_docs = json.loads(response_docs)
                except json.JSONDecodeError:
                    response_docs = {}
 
            rfp_responses_section = response_docs.get('rfpResponses')
            if not isinstance(rfp_responses_section, dict):
                rfp_responses_section = {}
 
            criteria_key = str(criteria_id)
            criteria_entry = rfp_responses_section.get(criteria_key)
 
            if isinstance(criteria_entry, str):
                criteria_entry = {
                    'htmlContent': criteria_entry,
                    'attachments': []
                }
            elif not isinstance(criteria_entry, dict):
                criteria_entry = {}
 
            attachments = criteria_entry.get('attachments')
            if not isinstance(attachments, list):
                attachments = []
 
            attachments.append({
                'id': attachment_payload['id'],
                'url': attachment_payload['url'],
                'fileName': attachment_payload['fileName'],
                'originalFilename': attachment_payload['originalFilename'],
                'fileSize': attachment_payload['fileSize'],
                'contentType': attachment_payload['contentType'],
                'uploadedAt': attachment_payload['uploadedAt'],
                'isImage': attachment_payload['isImage']
            })
 
            criteria_entry['attachments'] = attachments
            rfp_responses_section[criteria_key] = criteria_entry
            response_docs['rfpResponses'] = rfp_responses_section
 
            response_record.response_documents = response_docs
            response_record.last_saved_at = timezone.now()
            response_record.save(update_fields=['response_documents', 'last_saved_at'])
 
            attachment_payload['responseId'] = response_record.response_id
 
        return JsonResponse({
            'success': True,
            'message': 'Attachment uploaded successfully',
            'attachment': attachment_payload
        })
 
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Failed to upload response asset: {str(e)}")
        print(error_traceback)
        return JsonResponse({
            'success': False,
            'error': f'Failed to upload attachment: {str(e)}'
        }, status=500)
 
 
 

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@rbac_rfp_optional('view_rfp')
def check_submission_status(request):
    """
    Check if a submission exists for the given parameters
    """
    try:
        rfp_id = request.GET.get('rfpId')
        vendor_id = request.GET.get('vendorId')
        invitation_id = request.GET.get('invitationId')
        
        if not rfp_id:
            return JsonResponse({
                'success': False,
                'error': 'RFP ID is required'
            }, status=400)
        
        # Check for existing submission - only treat as submitted if evaluation_status is 'SUBMITTED'
        response = None
        if vendor_id:
            response = RFPResponse.objects.filter(
                rfp_id=rfp_id,
                vendor_id=vendor_id
            ).first()
        elif invitation_id:
            # Handle both numeric invitation_id and string tokens
            try:
                # Try to find by numeric invitation_id first
                numeric_invitation_id = int(invitation_id)
                response = RFPResponse.objects.filter(
                    invitation_id=numeric_invitation_id
                ).first()
            except (ValueError, TypeError):
                # If not numeric, try to find by unique_token in VendorInvitation
                try:
                    invitation = VendorInvitation.objects.filter(
                        unique_token=invitation_id
                    ).first()
                    if invitation:
                        response = RFPResponse.objects.filter(
                            invitation_id=invitation.invitation_id
                        ).first()
                except Exception as e:
                    print(f"Error finding invitation by token: {e}")
                    response = None
        
        if response:
            # Only consider it submitted if the evaluation_status is 'SUBMITTED'
            is_actually_submitted = response.evaluation_status == 'SUBMITTED'
            
            return JsonResponse({
                'success': True,
                'submitted': is_actually_submitted,
                'response_id': response.response_id,
                'evaluation_status': response.evaluation_status,
                'submitted_at': response.submission_date.isoformat() if response.submission_date else None,
                'is_draft': not is_actually_submitted
            })
        else:
            return JsonResponse({
                'success': True,
                'submitted': False,
                'message': 'No submission found'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to check submission status: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_invitation_details(request, invitation_id):
    """
    Get invitation details for prefilling the form
    """
    print(f"[DEBUG] get_invitation_details called with invitation_id: {invitation_id}")
    print(f"[DEBUG] Request method: {request.method}")
    print(f"[DEBUG] Request path: {request.path}")
    print(f"[DEBUG] Request META: {dict(request.META)}")
    try:
        # Try to find invitation by unique_token first (for string tokens like INV12345)
        try:
            invitation = VendorInvitation.objects.only(
                'invitation_id', 'unique_token', 'vendor_name', 'vendor_email', 
                'vendor_phone', 'company_name', 'invitation_status', 'rfp_id'
            ).get(unique_token=invitation_id)
        except VendorInvitation.DoesNotExist:
            # Try to find by numeric invitation_id
            try:
                numeric_id = int(invitation_id)
                invitation = VendorInvitation.objects.only(
                    'invitation_id', 'unique_token', 'vendor_name', 'vendor_email', 
                    'vendor_phone', 'company_name', 'invitation_status', 'rfp_id'
                ).get(invitation_id=numeric_id)
            except (ValueError, VendorInvitation.DoesNotExist):
                return JsonResponse({
                    'success': False,
                    'error': f'Invitation not found: {invitation_id}'
                }, status=404)
        
        # Check if invitation is valid
        if invitation.invitation_status in ['DECLINED', 'CANCELLED']:
            return JsonResponse({
                'success': False,
                'error': 'This invitation is no longer valid'
            }, status=400)
        
        # Check if response already exists
        existing_response = RFPResponse.objects.filter(invitation=invitation).first()
        
        # Get RFP information separately
        from rfp.models import RFP
        rfp = RFP.objects.get(rfp_id=invitation.rfp_id)
        
        return JsonResponse({
            'success': True,
            'invitation': {
                'invitation_id': invitation.invitation_id,
                'vendor_name': invitation.vendor_name,
                'vendor_email': invitation.vendor_email,
                'vendor_phone': invitation.vendor_phone,
                'company_name': invitation.company_name,
                'invitation_status': invitation.invitation_status,
                'custom_message': getattr(invitation, 'custom_message', None),
                'rfp_title': rfp.rfp_title,
                'rfp_number': rfp.rfp_number,
                'submission_deadline': rfp.submission_deadline.isoformat() if rfp.submission_deadline else None,
                'rfp_description': rfp.description
            },
            'existing_response': {
                'response_id': existing_response.response_id if existing_response else None,
                'submission_status': existing_response.submission_status if existing_response else None,
                'submitted_at': existing_response.submitted_at.isoformat() if existing_response and existing_response.submitted_at else None
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to fetch invitation details: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def test_endpoint(request):
    """
    Simple test endpoint to check if the issue is general
    """
    return JsonResponse({
        'success': True,
        'message': 'Test endpoint working',
        'method': request.method,
        'path': request.path
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@rbac_rfp_optional('view_rfp')
def test_risk_analysis(request):
    """
    Test endpoint to manually trigger risk analysis for a specific RFP response
    Usage: POST /api/rfp/test-risk-analysis/ with {"response_id": 123}
    """
    try:
        data = json.loads(request.body)
        response_id = data.get('response_id')
        
        if not response_id:
            return JsonResponse({
                'success': False,
                'error': 'response_id is required'
            }, status=400)
        
        # Get the RFP response
        try:
            rfp_response = RFPResponse.objects.get(response_id=response_id)
        except RFPResponse.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'RFP response not found: {response_id}'
            }, status=404)
        
        print(f"[TEST] Manual risk analysis triggered for response {response_id}")
        
        # Trigger risk analysis
        risk_analysis_result = trigger_rfp_risk_analysis(rfp_response)
        
        return JsonResponse({
            'success': True,
            'message': f'Risk analysis completed for response {response_id}',
            'result': risk_analysis_result,
            'response_info': {
                'response_id': rfp_response.response_id,
                'rfp_id': rfp_response.rfp_id,
                'submitted_by': rfp_response.submitted_by,
                'submission_date': rfp_response.submission_date.isoformat() if rfp_response.submission_date else None
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        return JsonResponse({
            'success': False,
            'error': f'Failed to test risk analysis: {str(e)}',
            'traceback': error_traceback
        }, status=500)


@api_view(['GET'])
@authentication_classes([])  # Allow anonymous access for vendor portal
@permission_classes([AllowAny])  # Allow anonymous access for vendor portal
# Note: Removed @rbac_rfp_optional decorator to allow fully public access for vendor portal
def get_rfp_details(request):
    """
    Get RFP details for prefilling the form using new query parameter format
    Public endpoint for vendor portal - no authentication required
    """
    logger.info(f'[get_rfp_details] Request received - Method: {request.method}, Path: {request.path}')
    try:
        # Get parameters from query string
        rfp_id = request.GET.get('rfpId')
        vendor_id = request.GET.get('vendorId', '')
        org = request.GET.get('org', '')
        vendor_name = request.GET.get('vendorName', '')
        contact_email = request.GET.get('contactEmail', '')
        contact_phone = request.GET.get('contactPhone', '')
        
        logger.info(f'[get_rfp_details] Query parameters - rfpId: {rfp_id}, vendorId: {vendor_id}, org: {org}, vendorName: {vendor_name}')
        
        if not rfp_id:
            logger.warning(f'[get_rfp_details] Missing rfpId parameter')
            return JsonResponse({
                'success': False,
                'error': 'rfpId parameter is required'
            }, status=400)
        
        # Get RFP details
        from rfp.models import RFP, RFPTypeCustomFields
        logger.info(f'[get_rfp_details] Fetching RFP with rfp_id: {rfp_id}')
        try:
            rfp = RFP.objects.get(rfp_id=rfp_id)
            logger.info(f'[get_rfp_details] RFP found - rfp_id: {rfp.rfp_id}, rfp_number: {rfp.rfp_number}, rfp_title: {rfp.rfp_title}, rfp_type: {rfp.rfp_type}')
        except RFP.DoesNotExist:
            logger.error(f'[get_rfp_details] RFP not found with rfp_id: {rfp_id}')
            return JsonResponse({
                'success': False,
                'error': f'RFP not found: {rfp_id}'
            }, status=404)
        
        # Fetch response_fields based on rfp_type from the RFP record
        response_fields = None
        rfp_type_value = rfp.rfp_type  # Get rfp_type directly from the RFP object
        if rfp_type_value:
            try:
                # Strip whitespace and try exact match first
                rfp_type_value = rfp_type_value.strip() if isinstance(rfp_type_value, str) else str(rfp_type_value)
                rfp_type_record = RFPTypeCustomFields.objects.filter(rfp_type=rfp_type_value).first()
                if rfp_type_record and rfp_type_record.response_fields:
                    response_fields = rfp_type_record.response_fields
                    logger.info(f'Successfully fetched response_fields for rfp_type: {rfp_type_value}')
                else:
                    logger.info(f'No response_fields found for rfp_type: {rfp_type_value}')
            except Exception as e:
                logger.error(f'Error fetching response_fields for rfp_type {rfp_type_value}: {str(e)}', exc_info=True)
        else:
            logger.warning(f'RFP {rfp_id} has no rfp_type set')
        
        # Prepare response data
        logger.info(f'[get_rfp_details] Preparing response data - response_fields present: {response_fields is not None}')
        response_data = {
            'success': True,
            'rfp': {
                'rfp_id': rfp.rfp_id,
                'rfp_title': rfp.rfp_title,
                'rfp_number': rfp.rfp_number,
                'description': rfp.description,
                'rfp_type': rfp_type_value,
                'category': getattr(rfp, 'category', None),
                'submission_deadline': rfp.submission_deadline.isoformat() if rfp.submission_deadline else None,
                'estimated_value': float(rfp.estimated_value) if rfp.estimated_value else None,
                'currency': rfp.currency,
                'budget_range_min': float(rfp.budget_range_min) if rfp.budget_range_min else None,
                'budget_range_max': float(rfp.budget_range_max) if rfp.budget_range_max else None,
                'status': rfp.status,
                'criticality_level': getattr(rfp, 'criticality_level', None),
                'documents': rfp.documents,  # Include documents field
                'response_fields': response_fields  # Include dynamic response fields
            },
            'vendor': {
                'vendor_id': vendor_id,
                'org': org,
                'vendor_name': vendor_name,
                'contact_email': contact_email,
                'contact_phone': contact_phone
            }
        }
        
        logger.debug(f'[get_rfp_details] Response data structure - rfp.response_fields type: {type(response_fields)}, is None: {response_fields is None}')
        if response_fields:
            logger.debug(f'[get_rfp_details] Response fields content: {response_fields}')
        
        # If vendor_id is provided, try to get additional vendor details
        if vendor_id:
            logger.info(f'[get_rfp_details] Fetching vendor details for vendor_id: {vendor_id}')
            try:
                vendor = Vendor.objects.get(vendor_id=vendor_id)
                logger.info(f'[get_rfp_details] Vendor found - vendor_id: {vendor.vendor_id}, company_name: {vendor.company_name}')
                response_data['vendor'].update({
                    'company_name': vendor.company_name,
                    'legal_name': vendor.legal_name,
                    'business_type': vendor.business_type,
                    'website': vendor.website,
                    'industry_sector': vendor.industry_sector,
                    'headquarters_country': vendor.headquarters_country,
                    'headquarters_address': vendor.headquarters_address,
                    'description': vendor.description
                })
            except Vendor.DoesNotExist:
                logger.warning(f'[get_rfp_details] Vendor not found with vendor_id: {vendor_id}')
                pass  # Use provided parameters only
        
        logger.info(f'[get_rfp_details] Returning response - success: True, rfp_id: {rfp.rfp_id}, has_response_fields: {response_fields is not None}')
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to fetch RFP details: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@rbac_rfp_optional('view_rfp')
def get_open_rfp_details(request, rfp_number):
    """
    Get details for open RFP (no invitation required)
    """
    logger.info(f'[get_open_rfp_details] Request received - rfp_number: {rfp_number}, Method: {request.method}, Path: {request.path}')
    try:
        from rfp.models import RFPTypeCustomFields
        logger.info(f'[get_open_rfp_details] Fetching RFP with rfp_number: {rfp_number}')
        rfp = get_object_or_404(RFP, rfp_number=rfp_number)
        logger.info(f'[get_open_rfp_details] RFP found - rfp_id: {rfp.rfp_id}, rfp_number: {rfp.rfp_number}, rfp_title: {rfp.rfp_title}, rfp_type: {rfp.rfp_type}, status: {rfp.status}')
        
        # Check if RFP is open for submissions
        if rfp.status not in ['PUBLISHED', 'SUBMISSION_OPEN']:
            return JsonResponse({
                'success': False,
                'error': 'This RFP is not currently open for submissions'
            }, status=400)
        
        # Check if submission deadline has passed
        if rfp.submission_deadline and rfp.submission_deadline < timezone.now():
            return JsonResponse({
                'success': False,
                'error': 'The submission deadline for this RFP has passed'
            }, status=400)
        
        # Fetch response_fields based on rfp_type from the RFP record
        response_fields = None
        rfp_type_value = rfp.rfp_type  # Get rfp_type directly from the RFP object
        logger.info(f'[get_open_rfp_details] RFP type from record: {rfp_type_value} (type: {type(rfp_type_value)})')
        
        if rfp_type_value:
            try:
                # Strip whitespace and try exact match first
                rfp_type_value = rfp_type_value.strip() if isinstance(rfp_type_value, str) else str(rfp_type_value)
                logger.info(f'[get_open_rfp_details] Processing rfp_type: "{rfp_type_value}" (after strip)')
                
                logger.info(f'[get_open_rfp_details] Querying RFPTypeCustomFields for rfp_type: "{rfp_type_value}"')
                rfp_type_record = RFPTypeCustomFields.objects.filter(rfp_type=rfp_type_value).first()
                
                if rfp_type_record:
                    logger.info(f'[get_open_rfp_details] Found RFPTypeCustomFields record - rfp_type_id: {rfp_type_record.rfp_type_id}, has response_fields: {bool(rfp_type_record.response_fields)}')
                    if rfp_type_record.response_fields:
                        response_fields = rfp_type_record.response_fields
                        logger.info(f'[get_open_rfp_details] Successfully fetched response_fields for rfp_type: {rfp_type_value}')
                        logger.debug(f'[get_open_rfp_details] Response fields data: {response_fields}')
                    else:
                        logger.info(f'[get_open_rfp_details] RFPTypeCustomFields record found but response_fields is empty/null for rfp_type: {rfp_type_value}')
                else:
                    logger.info(f'[get_open_rfp_details] No RFPTypeCustomFields record found for rfp_type: {rfp_type_value}')
                    existing_types = list(RFPTypeCustomFields.objects.values_list('rfp_type', flat=True).distinct())
                    logger.debug(f'[get_open_rfp_details] Available rfp_types in database: {existing_types}')
            except Exception as e:
                logger.error(f'[get_open_rfp_details] Error fetching response_fields for rfp_type {rfp_type_value}: {str(e)}', exc_info=True)
        else:
            logger.warning(f'[get_open_rfp_details] RFP {rfp.rfp_number} has no rfp_type set (rfp_type is None or empty)')
        
        logger.info(f'[get_open_rfp_details] Preparing response - response_fields present: {response_fields is not None}')
        response_data = {
            'success': True,
            'rfp': {
                'rfp_id': rfp.rfp_id,
                'rfp_title': rfp.rfp_title,
                'rfp_number': rfp.rfp_number,
                'description': rfp.description,
                'rfp_type': rfp_type_value,
                'submission_deadline': rfp.submission_deadline.isoformat() if rfp.submission_deadline else None,
                'estimated_value': float(rfp.estimated_value) if rfp.estimated_value else None,
                'currency': rfp.currency,
                'budget_range_min': float(rfp.budget_range_min) if rfp.budget_range_min else None,
                'budget_range_max': float(rfp.budget_range_max) if rfp.budget_range_max else None,
                'status': rfp.status,
                'documents': rfp.documents,  # Include documents for open RFP
                'response_fields': response_fields  # Include dynamic response fields
            }
        }
        logger.debug(f'[get_open_rfp_details] Response data - rfp.response_fields type: {type(response_fields)}, is None: {response_fields is None}')
        if response_fields:
            logger.debug(f'[get_open_rfp_details] Response fields content: {response_fields}')
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f'[get_open_rfp_details] Exception occurred: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Failed to fetch RFP details: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@rbac_rfp_optional('view_rfp')
def get_open_rfp_by_id(request, rfp_id):
    """
    Get details for open RFP by ID (no invitation required)
    """
    logger.info(f'[get_open_rfp_by_id] Request received - rfp_id: {rfp_id}, Method: {request.method}, Path: {request.path}')
    try:
        from rfp.models import RFPTypeCustomFields
        logger.info(f'[get_open_rfp_by_id] Fetching RFP with rfp_id: {rfp_id}')
        rfp = get_object_or_404(RFP, rfp_id=rfp_id)
        logger.info(f'[get_open_rfp_by_id] RFP found - rfp_id: {rfp.rfp_id}, rfp_number: {rfp.rfp_number}, rfp_title: {rfp.rfp_title}, rfp_type: {rfp.rfp_type}, status: {rfp.status}')
        
        # Check if RFP is open for submissions - allow more statuses for open submissions
        allowed_statuses = ['PUBLISHED', 'SUBMISSION_OPEN', 'ACTIVE', 'OPEN', 'LIVE']
        if rfp.status not in allowed_statuses:
            return JsonResponse({
                'success': False,
                'error': f'This RFP is not currently open for submissions. Current status: {rfp.status}'
            }, status=400)
        
        # Check if submission deadline has passed
        if rfp.submission_deadline and rfp.submission_deadline < timezone.now():
            return JsonResponse({
                'success': False,
                'error': 'The submission deadline for this RFP has passed'
            }, status=400)
        
        # Fetch response_fields based on rfp_type from the RFP record
        response_fields = None
        rfp_type_value = rfp.rfp_type  # Get rfp_type directly from the RFP object
        logger.info(f'[get_open_rfp_by_id] RFP type from record: {rfp_type_value} (type: {type(rfp_type_value)})')
        
        if rfp_type_value:
            try:
                # Strip whitespace and try exact match first
                rfp_type_value = rfp_type_value.strip() if isinstance(rfp_type_value, str) else str(rfp_type_value)
                logger.info(f'[get_open_rfp_by_id] Processing rfp_type: "{rfp_type_value}" (after strip)')
                
                logger.info(f'[get_open_rfp_by_id] Querying RFPTypeCustomFields for rfp_type: "{rfp_type_value}"')
                rfp_type_record = RFPTypeCustomFields.objects.filter(rfp_type=rfp_type_value).first()
                
                if rfp_type_record:
                    logger.info(f'[get_open_rfp_by_id] Found RFPTypeCustomFields record - rfp_type_id: {rfp_type_record.rfp_type_id}, has response_fields: {bool(rfp_type_record.response_fields)}')
                    if rfp_type_record.response_fields:
                        response_fields = rfp_type_record.response_fields
                        logger.info(f'[get_open_rfp_by_id] Successfully fetched response_fields for rfp_type: {rfp_type_value}')
                        logger.debug(f'[get_open_rfp_by_id] Response fields data: {response_fields}')
                    else:
                        logger.info(f'[get_open_rfp_by_id] RFPTypeCustomFields record found but response_fields is empty/null for rfp_type: {rfp_type_value}')
                else:
                    logger.info(f'[get_open_rfp_by_id] No RFPTypeCustomFields record found for rfp_type: {rfp_type_value}')
                    existing_types = list(RFPTypeCustomFields.objects.values_list('rfp_type', flat=True).distinct())
                    logger.debug(f'[get_open_rfp_by_id] Available rfp_types in database: {existing_types}')
            except Exception as e:
                logger.error(f'[get_open_rfp_by_id] Error fetching response_fields for rfp_type {rfp_type_value}: {str(e)}', exc_info=True)
        else:
            logger.warning(f'[get_open_rfp_by_id] RFP {rfp_id} has no rfp_type set (rfp_type is None or empty)')
        
        logger.info(f'[get_open_rfp_by_id] Preparing response - response_fields present: {response_fields is not None}')
        response_data = {
            'success': True,
            'rfp': {
                'rfp_id': rfp.rfp_id,
                'rfp_title': rfp.rfp_title,
                'rfp_number': rfp.rfp_number,
                'description': rfp.description,
                'rfp_type': rfp_type_value,
                'submission_deadline': rfp.submission_deadline.isoformat() if rfp.submission_deadline else None,
                'estimated_value': float(rfp.estimated_value) if rfp.estimated_value else None,
                'currency': rfp.currency,
                'budget_range_min': float(rfp.budget_range_min) if rfp.budget_range_min else None,
                'budget_range_max': float(rfp.budget_range_max) if rfp.budget_range_max else None,
                'status': rfp.status,
                'documents': rfp.documents,  # Include documents for open RFP
                'response_fields': response_fields  # Include dynamic response fields
            }
        }
        logger.debug(f'[get_open_rfp_by_id] Response data - rfp.response_fields type: {type(response_fields)}, is None: {response_fields is None}')
        if response_fields:
            logger.debug(f'[get_open_rfp_by_id] Response fields content: {response_fields}')
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f'[get_open_rfp_by_id] Exception occurred: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Failed to fetch RFP details: {str(e)}'
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('create_rfp')
def create_open_invitation(request, rfp_number):
    """
    Create a temporary invitation for open RFP submissions
    """
    try:
        rfp = get_object_or_404(RFP, rfp_number=rfp_number)
        
        # Check if RFP is open for submissions
        if rfp.status not in ['PUBLISHED', 'SUBMISSION_OPEN']:
            return JsonResponse({
                'success': False,
                'error': 'This RFP is not currently open for submissions'
            }, status=400)
        
        # Check if submission deadline has passed
        if rfp.submission_deadline and rfp.submission_deadline < timezone.now():
            return JsonResponse({
                'success': False,
                'error': 'The submission deadline for this RFP has passed'
            }, status=400)
        
        # Generate unique token for open submission
        unique_token = generate_invitation_id()
        
        # Create a temporary invitation for open RFP
        invitation = VendorInvitation.objects.create(
            rfp=rfp,
            vendor=None,  # No specific vendor for open RFPs
            vendor_email=None,
            vendor_name=None,
            vendor_phone=None,
            company_name=None,
            unique_token=unique_token,
            invitation_status='OPEN',
            is_matched_vendor=False,
            submission_source='open'
        )
        
        return JsonResponse({
            'success': True,
            'invitation': {
                'invitation_id': invitation.invitation_id,
                'unique_token': invitation.unique_token,
                'rfp_title': rfp.rfp_title,
                'rfp_number': rfp.rfp_number,
                'submission_deadline': rfp.submission_deadline.isoformat() if rfp.submission_deadline else None
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to create open invitation: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([])  # Allow anonymous access for vendor portal
@permission_classes([AllowAny])  # Allow anonymous access for vendor portal
# Note: Removed @rbac_rfp_optional decorator to allow fully public access for vendor portal
def get_rfp_evaluation_criteria(request, rfp_number):
    """
    Get evaluation criteria for an RFP
    Public endpoint for vendor portal - no authentication required
    """
    try:
        rfp = get_object_or_404(RFP, rfp_number=rfp_number)
        
        criteria = []
        try:
            for criterion in rfp.evaluation_criteria.all():
                criteria.append({
                    'criteria_id': criterion.criteria_id,
                    'criteria_name': criterion.criteria_name,
                    'criteria_description': criterion.criteria_description,
                    'weight_percentage': float(criterion.weight_percentage),
                    'evaluation_type': criterion.evaluation_type,
                    'is_mandatory': criterion.is_mandatory,
                    'min_score': float(criterion.min_score) if criterion.min_score else None,
                    'max_score': float(criterion.max_score) if criterion.max_score else None,
                    'min_word_count': criterion.min_word_count,
                    'display_order': criterion.display_order
                })
        except Exception as e:
            print(f"Error loading evaluation criteria: {e}")
            criteria = []
        
        return JsonResponse({
            'success': True,
            'criteria': criteria,
            'rfp_title': rfp.rfp_title,
            'rfp_number': rfp.rfp_number
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to fetch evaluation criteria: {str(e)}'
        }, status=500)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@rbac_rfp_optional('create_rfp_response')
def save_draft_response(request):
    """
    Save or update a draft RFP response
    """
    try:
        data = json.loads(request.body)
        
        rfp_id = data.get('rfpId')
        vendor_id = data.get('vendorId')
        invitation_id = data.get('invitationId')
        
        # Convert vendor_id to integer if it's a string
        if vendor_id and isinstance(vendor_id, str):
            try:
                vendor_id = int(vendor_id)
            except ValueError:
                vendor_id = None
        
        org = data.get('org', '')
        vendor_name = data.get('vendorName', '')
        contact_email = data.get('contactEmail', '')
        contact_phone = data.get('contactPhone', '')
        proposal_data = data.get('proposalData', {})
        submission_status = data.get('submissionStatus', 'DRAFT')
        completion_percentage = data.get('completionPercentage', 0)
        
        # CRITICAL: Extract UTM parameters for tracking
        utm_params = data.get('utmParameters', {})
        
        # CRITICAL: vendor_id must come from invitation - no fallback lookups
        # Invitation must be provided and will contain the vendor_id
        
        # Convert completion_percentage to proper decimal or None
        if completion_percentage is not None:
            try:
                completion_percentage = float(completion_percentage)
            except (ValueError, TypeError):
                completion_percentage = None
        else:
            completion_percentage = None
        
        # Validate required fields
        if not vendor_name or not contact_email:
            return JsonResponse({
                'success': False,
                'error': 'Vendor name and contact email are required'
            }, status=400)
        
        # Get client information
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        with transaction.atomic():
            # Get RFP
            from rfp.models import RFP
            try:
                rfp = RFP.objects.get(rfp_id=rfp_id)
            except RFP.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'RFP not found: {rfp_id}'
                }, status=404)
            
            # Get invitation if invitation_id is provided (for both update and create)
            # CRITICAL: Extract invitation and vendor_id from it
            invitation = None
            if invitation_id:
                try:
                    # Try to find by unique_token first (for string tokens like INV12345)
                    invitation = VendorInvitation.objects.select_related('vendor').filter(unique_token=invitation_id).first()
                    if not invitation:
                        # Try to find by numeric invitation_id
                        try:
                            numeric_id = int(invitation_id)
                            invitation = VendorInvitation.objects.select_related('vendor').get(invitation_id=numeric_id)
                        except (ValueError, VendorInvitation.DoesNotExist):
                            pass
                    
                    # CRITICAL: Extract vendor_id from invitation if found and not provided
                    if invitation:
                        print(f"[CRITICAL] Found invitation in save_draft: invitation_id={invitation.invitation_id}")
                        if not vendor_id:
                            if invitation.vendor:
                                vendor_id = invitation.vendor.vendor_id
                                print(f"[CRITICAL] Extracted vendor_id from invitation.vendor: {vendor_id}")
                            elif hasattr(invitation, 'unmatched_vendor_id') and invitation.unmatched_vendor_id:
                                vendor_id = invitation.unmatched_vendor_id
                                print(f"[CRITICAL] Extracted unmatched_vendor_id from invitation: {vendor_id}")
                        else:
                            # Override with invitation vendor_id if available (more reliable)
                            if invitation.vendor:
                                vendor_id = invitation.vendor.vendor_id
                                print(f"[CRITICAL] Overriding vendor_id with invitation.vendor.vendor_id: {vendor_id}")
                            elif hasattr(invitation, 'unmatched_vendor_id') and invitation.unmatched_vendor_id:
                                vendor_id = invitation.unmatched_vendor_id
                                print(f"[CRITICAL] Overriding vendor_id with invitation.unmatched_vendor_id: {vendor_id}")
                except Exception as e:
                    logger.warning(f'[save_draft_response] Error finding invitation: {e}')
                    pass  # Continue without invitation
            
            # CRITICAL: vendor_id MUST come from invitation - no fallbacks
            if not vendor_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Vendor ID must come from invitation. Invitation does not have a valid vendor_id.'
                }, status=400)
            
            # Check if any response already exists (draft or submitted)
            # vendor_id MUST come from invitation - no fallbacks
            existing_response = None
            if vendor_id:
                existing_response = RFPResponse.objects.filter(
                    rfp=rfp,
                    vendor_id=vendor_id
                ).first()
            else:
                # vendor_id is required - should have been set from invitation above
                return JsonResponse({
                    'success': False,
                    'error': 'Vendor ID is required. Must come from invitation.'
                }, status=400)
            
            if existing_response:
                # Update existing draft with complete nested structure
                logger.info(f'[save_draft_response] Updating existing draft - response_id: {existing_response.response_id}')
                
                # Set invitation_id if we found one
                if invitation:
                    existing_response.invitation_id = invitation.invitation_id
                    logger.info(f'[save_draft_response] Set invitation_id for existing draft: {invitation.invitation_id}')
                
                # Set vendor_id if we have one
                if vendor_id:
                    existing_response.vendor_id = vendor_id
                    logger.info(f'[save_draft_response] Set vendor_id for existing draft: {vendor_id}')
                
                # Build complete response_documents structure from proposal_data
                response_documents = {}
                if proposal_data and isinstance(proposal_data, dict):
                    # Add companyInfo
                    if proposal_data.get('companyInfo'):
                        response_documents['companyInfo'] = proposal_data.get('companyInfo')
                    
                    # Add financialInfo
                    if proposal_data.get('financialInfo'):
                        response_documents['financialInfo'] = proposal_data.get('financialInfo')
                    
                    # Add responses/rfpResponses
                    if proposal_data.get('responses'):
                        response_documents['rfpResponses'] = proposal_data.get('responses')
                    
                    # Add teamInfo
                    if proposal_data.get('keyPersonnel'):
                        response_documents['teamInfo'] = {
                            'keyPersonnel': proposal_data.get('keyPersonnel')
                        }
                    
                    # Add dynamicFields
                    if proposal_data.get('dynamicFields'):
                        response_documents['dynamicFields'] = proposal_data.get('dynamicFields')
                        logger.info(f'[save_draft_response] Added dynamicFields to draft: {list(proposal_data.get("dynamicFields", {}).keys())}')
                    
                    # Add documents
                    if proposal_data.get('documents'):
                        response_documents['uploadedDocuments'] = proposal_data.get('documents')
                
                # Ensure vendor contact info is in companyInfo
                if 'companyInfo' not in response_documents:
                    response_documents['companyInfo'] = {}
                if not response_documents['companyInfo'].get('vendor_name') and vendor_name:
                    response_documents['companyInfo']['vendor_name'] = vendor_name
                if not response_documents['companyInfo'].get('contact_email') and contact_email:
                    response_documents['companyInfo']['contact_email'] = contact_email
                if not response_documents['companyInfo'].get('contact_phone') and contact_phone:
                    response_documents['companyInfo']['contact_phone'] = contact_phone
                if not response_documents['companyInfo'].get('org') and org:
                    response_documents['companyInfo']['org'] = org
                
                logger.debug(f'[save_draft_response] Complete response_documents structure: {response_documents}')
                existing_response.response_documents = response_documents
                
                existing_response.completion_percentage = completion_percentage
                existing_response.last_saved_at = timezone.now()
                
                # CRITICAL: Store UTM parameters in external_submission_data for drafts too
                if utm_params:
                    existing_response.external_submission_data = {
                        'utm_parameters': utm_params,
                        'submission_source': 'draft',
                        'ip_address': ip_address if ip_address else None,
                        'user_agent': user_agent if user_agent else None,
                        'submission_timestamp': timezone.now().isoformat()
                    }
                    print(f"[CRITICAL] Stored UTM parameters in draft: {utm_params}")
                
                # FINAL SAFETY CHECK: Ensure IDs are saved
                if invitation and existing_response.invitation_id != invitation.invitation_id:
                    existing_response.invitation_id = invitation.invitation_id
                    print(f"[FINAL SAFETY] Force updating invitation_id to {invitation.invitation_id} in draft")
                
                # Determine final vendor_id for safety check
                final_vendor_id_draft = vendor_id
                if invitation:
                    if invitation.vendor:
                        final_vendor_id_draft = invitation.vendor.vendor_id
                    elif hasattr(invitation, 'unmatched_vendor_id') and invitation.unmatched_vendor_id:
                        final_vendor_id_draft = invitation.unmatched_vendor_id
                
                if final_vendor_id_draft and existing_response.vendor_id != final_vendor_id_draft:
                    existing_response.vendor_id = final_vendor_id_draft
                    print(f"[FINAL SAFETY] Force updating vendor_id to {final_vendor_id_draft} in draft")
                
                existing_response.save()
                print(f"[FINAL SAFETY] Saved IDs to draft response {existing_response.response_id}: vendor_id={existing_response.vendor_id}, invitation_id={existing_response.invitation_id}")
                response_id = existing_response.response_id
            else:
                # Create new draft
                # (invitation is already retrieved above)
                
                # Build complete response_documents structure for new draft
                response_documents = {}
                if proposal_data and isinstance(proposal_data, dict):
                    # Add companyInfo
                    if proposal_data.get('companyInfo'):
                        response_documents['companyInfo'] = proposal_data.get('companyInfo')
                    
                    # Add financialInfo
                    if proposal_data.get('financialInfo'):
                        response_documents['financialInfo'] = proposal_data.get('financialInfo')
                    
                    # Add responses/rfpResponses
                    if proposal_data.get('responses'):
                        response_documents['rfpResponses'] = proposal_data.get('responses')
                    
                    # Add teamInfo
                    if proposal_data.get('keyPersonnel'):
                        response_documents['teamInfo'] = {
                            'keyPersonnel': proposal_data.get('keyPersonnel')
                        }
                    
                    # Add dynamicFields
                    if proposal_data.get('dynamicFields'):
                        response_documents['dynamicFields'] = proposal_data.get('dynamicFields')
                        logger.info(f'[save_draft_response] Added dynamicFields to new draft: {list(proposal_data.get("dynamicFields", {}).keys())}')
                    
                    # Add documents
                    if proposal_data.get('documents'):
                        response_documents['uploadedDocuments'] = proposal_data.get('documents')
                
                # Ensure vendor contact info is in companyInfo
                if 'companyInfo' not in response_documents:
                    response_documents['companyInfo'] = {}
                if vendor_name:
                    response_documents['companyInfo']['vendor_name'] = vendor_name
                if contact_email:
                    response_documents['companyInfo']['contact_email'] = contact_email
                if contact_phone:
                    response_documents['companyInfo']['contact_phone'] = contact_phone
                if org:
                    response_documents['companyInfo']['org'] = org
                
                logger.info(f'[save_draft_response] Creating new draft with complete response_documents structure')
                logger.debug(f'[save_draft_response] Response documents: {response_documents}')
                
                # Determine final IDs for draft
                final_invitation_id_draft = invitation.invitation_id if invitation else None
                final_vendor_id_draft = vendor_id
                
                if invitation:
                    if invitation.vendor:
                        final_vendor_id_draft = invitation.vendor.vendor_id
                        print(f"[CRITICAL] Using vendor_id from invitation.vendor in draft: {final_vendor_id_draft}")
                    elif hasattr(invitation, 'unmatched_vendor_id') and invitation.unmatched_vendor_id:
                        final_vendor_id_draft = invitation.unmatched_vendor_id
                        print(f"[CRITICAL] Using unmatched_vendor_id from invitation in draft: {final_vendor_id_draft}")
                
                # CRITICAL: vendor_id MUST come from invitation - no fallbacks
                if not final_vendor_id_draft:
                    return JsonResponse({
                        'success': False,
                        'error': 'Vendor ID must come from invitation. Cannot create draft without valid vendor_id from invitation.'
                    }, status=400)
                
                print(f"[CRITICAL] Creating draft with vendor_id={final_vendor_id_draft}, invitation_id={final_invitation_id_draft}")
                
                # CRITICAL: Prepare external_submission_data with UTM parameters
                external_data = {
                    'submission_source': 'draft',
                    'ip_address': ip_address if ip_address else None,
                    'user_agent': user_agent if user_agent else None,
                    'submission_timestamp': timezone.now().isoformat()
                }
                if utm_params:
                    external_data['utm_parameters'] = utm_params
                    print(f"[CRITICAL] Storing UTM parameters in new draft: {utm_params}")
                
                new_response = RFPResponse.objects.create(
                    rfp=rfp,
                    vendor_id=final_vendor_id_draft,
                    invitation_id=final_invitation_id_draft,
                    response_documents=response_documents,
                    completion_percentage=completion_percentage,
                    last_saved_at=timezone.now(),
                    external_submission_data=external_data if utm_params or ip_address or user_agent else None
                )
                
                # FINAL SAFETY CHECK: Ensure IDs are saved in draft
                if invitation and new_response.invitation_id != invitation.invitation_id:
                    new_response.invitation_id = invitation.invitation_id
                    new_response.save()
                    print(f"[FINAL SAFETY] Updated invitation_id in draft: {invitation.invitation_id}")
                
                print(f"[FINAL SAFETY] Draft created with IDs: vendor_id={new_response.vendor_id}, invitation_id={new_response.invitation_id}")
                response_id = new_response.response_id
            
            return JsonResponse({
                'success': True,
                'message': 'Draft saved successfully',
                'response_id': response_id,
                'last_saved_at': timezone.now().isoformat()
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to save draft: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@rbac_rfp_optional('view_rfp')
def get_draft_response(request, rfp_id):
    """
    Get existing draft response for an RFP
    """
    try:
        vendor_id = request.GET.get('vendorId')
        invitation_id = request.GET.get('invitationId')
        
        # Get RFP first
        from rfp.models import RFP
        try:
            rfp = RFP.objects.get(rfp_id=rfp_id)
        except RFP.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'RFP not found: {rfp_id}'
            }, status=404)
        
        # Find existing draft - handle both vendor_id and invitation_id
        draft_response = None
        if vendor_id:
            draft_response = RFPResponse.objects.filter(
                rfp=rfp,
                vendor_id=vendor_id
            ).first()
        elif invitation_id:
            # Handle both numeric invitation_id and string tokens
            try:
                # Try to find by numeric invitation_id first
                numeric_invitation_id = int(invitation_id)
                draft_response = RFPResponse.objects.filter(
                    rfp=rfp,
                    invitation_id=numeric_invitation_id
                ).first()
            except (ValueError, TypeError):
                # If not numeric, try to find by unique_token in VendorInvitation
                try:
                    invitation = VendorInvitation.objects.filter(
                        unique_token=invitation_id
                    ).first()
                    if invitation:
                        draft_response = RFPResponse.objects.filter(
                            rfp=rfp,
                            invitation_id=invitation.invitation_id
                        ).first()
                except Exception as e:
                    print(f"Error finding invitation by token: {e}")
                    draft_response = None
        
        if not draft_response:
            return JsonResponse({
                'success': True,
                'draft': None,
                'message': 'No draft found'
            })
        
        return JsonResponse({
            'success': True,
            'draft': {
                'response_id': draft_response.response_id,
                'proposal_data': draft_response.response_documents,
                'submission_status': None,
                'completion_percentage': float(draft_response.completion_percentage) if draft_response.completion_percentage else 0,
                'last_saved_at': draft_response.last_saved_at.isoformat() if draft_response.last_saved_at else None,
                'created_at': draft_response.submission_date.isoformat() if draft_response.submission_date else None,
                'updated_at': draft_response.last_saved_at.isoformat() if draft_response.last_saved_at else None
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to fetch draft: {str(e)}'
        }, status=500)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@rbac_rfp_optional('create_rfp_response')
def upload_document(request):
    """
    Upload document for RFP response to S3
    """
    try:
        # Get form data
        file = request.FILES.get('file')
        document_type = request.POST.get('documentType')
        rfp_id = request.POST.get('rfpId')
        vendor_id = request.POST.get('vendorId')
       
        if not file or not document_type or not rfp_id:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
       
        # Validate file type - expanded to support more document types
        allowed_types = [
            'application/pdf',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'image/jpeg',
            'image/png',
            'text/plain',
            'application/zip',
            'application/x-zip-compressed'
        ]
        if file.content_type not in allowed_types:
            return JsonResponse({
                'success': False,
                'error': 'Invalid file type. Allowed types: PDF, Excel, Word, Images, Text, ZIP files.'
            }, status=400)
       
        # Validate file size (50MB limit)
        max_size = 50 * 1024 * 1024
        if file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': 'File size exceeds 50MB limit'
            }, status=400)
       
        # Import S3 service
        from rfp.s3_service import get_s3_service
        import uuid
        import os
        import tempfile
       
        # Generate unique filename for S3 (replace forward slashes with underscores)
        file_extension = file.name.split('.')[-1]
        vendor_id_str = str(vendor_id) if vendor_id else '0'
        unique_filename = f"rfp_documents_{document_type}_{rfp_id}_{vendor_id_str}_{uuid.uuid4().hex[:8]}.{file_extension}"
       
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
            # Reset file pointer to beginning
            file.seek(0)
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
       
        try:
            # Upload to S3
            s3_service = get_s3_service()
            upload_result = s3_service.upload_file(
                file_path=temp_file_path,
                user_id=vendor_id_str if vendor_id else '1',  # Use '1' as default if no vendor_id
                custom_file_name=unique_filename,
                rfp_id=int(rfp_id)
            )
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
       
        if not upload_result.get('success'):
            return JsonResponse({
                'success': False,
                'error': f'S3 upload failed: {upload_result.get("error", "Unknown error")}'
            }, status=500)
       
        # Get S3 URL and key from response
        s3_url = upload_result.get('s3_url')
        s3_key = upload_result.get('s3_key')
        file_info = upload_result.get('file_info', {})
       
        # Get document name from request
        document_name = request.POST.get('document_name', file.name)
       
        # Save to S3Files table for merging capability
        from rfp.models import S3Files
        import uuid
       
        # Determine file extension
        file_extension = os.path.splitext(file.name)[1] or '.pdf'
        file_type = file_extension[1:] if file_extension.startswith('.') else file_extension
       
        # Create S3Files entry
        s3_file = S3Files.objects.create(
            url=s3_url,
            file_type=file_type,
            file_name=document_name,
            user_id=vendor_id_str if vendor_id else '1',
            metadata={
                'original_filename': file.name,
                'stored_filename': file_info.get('storedName', unique_filename),
                's3_key': s3_key,
                's3_bucket': file_info.get('bucket', ''),
                'rfp_id': int(rfp_id),
                'document_name': document_name,
                'file_size': file.size,
                'upload_operation_id': upload_result.get('operation_id'),
                'document_type': document_type,
                'vendor_id': vendor_id if vendor_id else None
            }
        )
       
        print(f"[SUCCESS] Document saved to S3Files with ID: {s3_file.id}")
       
        # Update or create RFP response with document info
        # Only update RFPResponse if vendor_id is provided (for invited vendors)
        # For open RFPs without vendor_id, we skip RFPResponse update
        if vendor_id:
            try:
                with transaction.atomic():
                    # Find existing response
                    response = RFPResponse.objects.filter(
                        rfp_id=rfp_id,
                        vendor_id=vendor_id
                    ).first()
                   
                    if response:
                        # Update existing response
                        if not response.document_urls:
                            response.document_urls = {}
                       
                        # Add document URL and metadata (including S3Files ID for merging)
                        response.document_urls[document_type] = {
                            'url': s3_url,
                            'key': s3_key,
                            'filename': file.name,
                            'size': file.size,
                            'content_type': file.content_type,
                            'upload_date': timezone.now().isoformat(),
                            'document_id': s3_file.id,  # Add S3Files ID for merging
                            's3_file_id': s3_file.id
                        }
                        response.save()
                        print(f"[SUCCESS] Updated RFPResponse with document {document_type}")
                    else:
                        # Create new response with document (only if RFP exists)
                        try:
                            from rfp.models import RFP
                            rfp = RFP.objects.get(rfp_id=rfp_id)
                           
                            RFPResponse.objects.create(
                                rfp=rfp,
                                vendor_id=vendor_id,
                                document_urls={
                                    document_type: {
                                        'url': s3_url,
                                        'key': s3_key,
                                        'filename': file.name,
                                        'size': file.size,
                                        'content_type': file.content_type,
                                        'upload_date': timezone.now().isoformat(),
                                        'document_id': s3_file.id,  # Add S3Files ID for merging
                                        's3_file_id': s3_file.id
                                    }
                                },
                                evaluation_status='DRAFT'  # Changed from 'SUBMITTED' to 'DRAFT' for new responses
                            )
                            print(f"[SUCCESS] Created new RFPResponse with document {document_type}")
                        except RFP.DoesNotExist:
                            print(f"[WARN] RFP {rfp_id} does not exist, skipping RFPResponse creation")
                            # Continue without RFPResponse - document is still saved in S3Files
                        except Exception as rfp_error:
                            print(f"[WARN] Error creating/updating RFPResponse: {str(rfp_error)}")
                            import traceback
                            traceback.print_exc()
                            # Continue without RFPResponse - document is still saved in S3Files
            except Exception as response_error:
                print(f"[WARN] Error updating RFPResponse: {str(response_error)}")
                import traceback
                traceback.print_exc()
                # Continue - document is still saved in S3Files, which is what we need for merging
        else:
            print(f"[INFO] No vendor_id provided, skipping RFPResponse update (document saved to S3Files only)")
       
        return JsonResponse({
            'success': True,
            'message': 'Document uploaded successfully to S3',
            'document_url': s3_url,
            'document_id': s3_file.id,  # Return S3Files ID for merging
            's3_file_id': s3_file.id,  # Alias for compatibility
            'document_type': document_type,
            's3_key': s3_key,
            'file_size': file.size,
            'filename': file.name,
            'document_name': document_name
        })
       
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Exception in upload_document: {str(e)}")
        print(f"[ERROR] Traceback: {error_traceback}")
        logger.error(f"Failed to upload document: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Failed to upload document: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@rbac_rfp_optional('view_rfp')
def list_documents(request, rfp_id):
    """
    List all documents for an RFP response
    """
    try:
        vendor_id = request.GET.get('vendorId')
        invitation_id = request.GET.get('invitationId')
        
        if not vendor_id and not invitation_id:
            return JsonResponse({
                'success': False,
                'error': 'Either Vendor ID or Invitation ID is required'
            }, status=400)
        
        # Find the response - handle both vendor_id and invitation_id
        response = None
        if vendor_id:
            response = RFPResponse.objects.filter(
                rfp_id=rfp_id,
                vendor_id=vendor_id
            ).first()
        elif invitation_id:
            # Handle both numeric invitation_id and string tokens
            try:
                # Try to find by numeric invitation_id first
                numeric_invitation_id = int(invitation_id)
                response = RFPResponse.objects.filter(
                    rfp_id=rfp_id,
                    invitation_id=numeric_invitation_id
                ).first()
            except (ValueError, TypeError):
                # If not numeric, try to find by unique_token in VendorInvitation
                try:
                    invitation = VendorInvitation.objects.filter(
                        unique_token=invitation_id
                    ).first()
                    if invitation:
                        response = RFPResponse.objects.filter(
                            rfp_id=rfp_id,
                            invitation_id=invitation.invitation_id
                        ).first()
                except Exception as e:
                    print(f"Error finding invitation by token: {e}")
                    response = None
        
        if not response:
            # If no response exists yet, return empty documents list instead of 404
            # This handles the case where vendor is accessing portal for the first time
            return JsonResponse({
                'success': True,
                'documents': {},
                'total_count': 0,
                'message': 'No RFP response found yet - returning empty documents list'
            })
        
        # Return document URLs
        documents = response.document_urls or {}
        
        return JsonResponse({
            'success': True,
            'documents': documents,
            'total_count': len(documents)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to list documents: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_rfp_responses(request):
    """
    Get all RFP responses for a specific RFP ID
    """
    try:
        rfp_id = request.GET.get('rfp_id')
        
        if not rfp_id:
            return JsonResponse({
                'success': False,
                'error': 'rfp_id parameter is required'
            }, status=400)
        
        # Get all responses for this RFP
        all_responses = RFPResponse.objects.filter(rfp_id=rfp_id).order_by('-submission_date')
        
        # Debug: Log all responses found
        print(f"DEBUG: Found {all_responses.count()} total responses for RFP {rfp_id}")
        for resp in all_responses:
            print(f"DEBUG: Response {resp.response_id} - Eval Status: {resp.evaluation_status}")
        
        # Filter for submitted responses (but also include other statuses for debugging)
        submitted_responses = all_responses.filter(evaluation_status='SUBMITTED')
        print(f"DEBUG: Found {submitted_responses.count()} responses with evaluation_status SUBMITTED")
        
        # For award phase, include all responses regardless of status
        # Use submitted responses, but fall back to all responses if none are submitted
        responses_to_use = all_responses  # Always use all responses for award phase
        
        response_data = []
        for response in responses_to_use:
            try:
                # Extract vendor information from response_documents
                response_documents = response.response_documents or {}
                vendor_name = response_documents.get('vendor_name', '')
                contact_email = response_documents.get('contact_email', '')
                contact_phone = response_documents.get('contact_phone', '')
                org = response_documents.get('org', '')
                
                response_data.append({
                    'response_id': response.response_id,
                    'rfp_id': response.rfp_id,
                    'vendor_id': response.vendor_id,
                    'vendor_name': vendor_name,
                    'org': org,  # Ensure org field is included
                    'contact_email': contact_email,
                    'contact_phone': contact_phone,
                    'proposal_data': response.response_documents,
                    'proposed_value': float(response.proposed_value) if response.proposed_value else None,
                    'evaluation_status': response.evaluation_status,
                    'submitted_at': response.submission_date.isoformat() if response.submission_date else None,
                    'technical_score': float(response.technical_score) if response.technical_score else None,
                    'commercial_score': float(response.commercial_score) if response.commercial_score else None,
                    'overall_score': float(response.overall_score) if response.overall_score else None,
                    'evaluation_date': response.evaluation_date.isoformat() if response.evaluation_date else None,
                    'evaluation_comments': response.evaluation_comments,
                    'response_documents': response.response_documents,
                    'document_urls': response.document_urls
                })
            except Exception as e:
                print(f"DEBUG: Error processing response {response.response_id}: {str(e)}")
                continue
        
        print(f"DEBUG: Returning {len(response_data)} responses")
        
        return JsonResponse({
            'success': True,
            'responses': response_data,
            'total_count': len(response_data),
            'debug_info': {
                'total_responses_found': all_responses.count(),
                'submitted_responses': submitted_responses.count(),
                'responses_returned': len(response_data),
                'note': 'All responses included for award phase'
            }
        })
        
    except Exception as e:
        print(f"DEBUG: Error in get_rfp_responses: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Failed to fetch RFP responses: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_rfp_response_by_id(request, response_id):
    """
    Get a specific RFP response by ID
    """
    try:
        response = RFPResponse.objects.get(response_id=response_id)
        
        # Extract vendor information from response_documents
        response_documents = response.response_documents or {}
        vendor_name = response_documents.get('vendor_name', '')
        contact_email = response_documents.get('contact_email', '')
        contact_phone = response_documents.get('contact_phone', '')
        org = response_documents.get('org', '')
        
        response_data = {
            'response_id': response.response_id,
            'rfp_id': response.rfp_id,
            'vendor_id': response.vendor_id,
            'vendor_name': vendor_name,
            'org': org,  # Ensure org field is included
            'contact_email': contact_email,
            'contact_phone': contact_phone,
            'proposal_data': response.response_documents,
            'proposed_value': float(response.proposed_value) if response.proposed_value else None,
            'evaluation_status': response.evaluation_status,
            'submitted_at': response.submission_date.isoformat() if response.submission_date else None,
            'technical_score': float(response.technical_score) if response.technical_score else None,
            'commercial_score': float(response.commercial_score) if response.commercial_score else None,
            'overall_score': float(response.overall_score) if response.overall_score else None,
            'evaluation_date': response.evaluation_date.isoformat() if response.evaluation_date else None,
            'evaluation_comments': response.evaluation_comments,
            'response_documents': response.response_documents,
            'document_urls': response.document_urls
        }
        
        return JsonResponse({
            'success': True,
            'data': response_data
        })
        
    except RFPResponse.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'RFP response not found: {response_id}'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to fetch RFP response: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@rbac_rfp_optional('view_rfp')
def download_document(request, rfp_id):
    """
    Download a specific document from S3
    """
    try:
        vendor_id = request.GET.get('vendorId')
        document_type = request.GET.get('documentType')
        
        if not vendor_id or not document_type:
            return JsonResponse({
                'success': False,
                'error': 'Vendor ID and document type are required'
            }, status=400)
        
        # Find the response
        response = RFPResponse.objects.filter(
            rfp_id=rfp_id,
            vendor_id=vendor_id
        ).first()
        
        if not response:
            return JsonResponse({
                'success': False,
                'error': 'RFP response not found'
            }, status=404)
        
        # Get document info
        documents = response.document_urls or {}
        if document_type not in documents:
            return JsonResponse({
                'success': False,
                'error': 'Document not found'
            }, status=404)
        
        document_info = documents[document_type]
        s3_key = document_info.get('key')
        
        if not s3_key:
            return JsonResponse({
                'success': False,
                'error': 'S3 key not found for document'
            }, status=404)
        
        # Download from S3
        from rfp.s3_service import get_s3_service
        s3_service = get_s3_service()
        
        download_result = s3_service.download_file(
            s3_key=s3_key,
            user_id=str(vendor_id)
        )
        
        if not download_result.get('success'):
            return JsonResponse({
                'success': False,
                'error': f'Download failed: {download_result.get("error", "Unknown error")}'
            }, status=500)
        
        # Return download URL or file content
        return JsonResponse({
            'success': True,
            'download_url': download_result.get('url'),
            'filename': document_info.get('filename'),
            'content_type': document_info.get('content_type'),
            'size': document_info.get('size')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to download document: {str(e)}'
        }, status=500)


@api_view(['DELETE'])
@authentication_classes([])
@permission_classes([AllowAny])
@rbac_rfp_optional('delete_rfp')
def delete_document(request, rfp_id):
    """
    Delete a specific document from S3 and database
    """
    try:
        data = json.loads(request.body)
        vendor_id = data.get('vendorId')
        document_type = data.get('documentType')
        
        if not vendor_id or not document_type:
            return JsonResponse({
                'success': False,
                'error': 'Vendor ID and document type are required'
            }, status=400)
        
        # Find the response
        response = RFPResponse.objects.filter(
            rfp_id=rfp_id,
            vendor_id=vendor_id
        ).first()
        
        if not response:
            return JsonResponse({
                'success': False,
                'error': 'RFP response not found'
            }, status=404)
        
        # Get document info
        documents = response.document_urls or {}
        if document_type not in documents:
            return JsonResponse({
                'success': False,
                'error': 'Document not found'
            }, status=404)
        
        document_info = documents[document_type]
        s3_key = document_info.get('key')
        
        # Delete from S3 if key exists
        if s3_key:
            from rfp.s3_service import get_s3_service
            s3_service = get_s3_service()
            
            delete_result = s3_service.delete_file(
                s3_key=s3_key,
                user_id=str(vendor_id)
            )
            
            if not delete_result.get('success'):
                return JsonResponse({
                    'success': False,
                    'error': f'S3 deletion failed: {delete_result.get("error", "Unknown error")}'
                }, status=500)
        
        # Remove from database
        del documents[document_type]
        response.document_urls = documents
        response.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Document deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to delete document: {str(e)}'
        }, status=500)
