"""
Views for RFI vendor invitations and responses (similar to RFP flow)
Updated: 2026-02-09 - Fixed acknowledge endpoint to accept GET requests
"""
import json
import time
import secrets
import logging
import re
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect as csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import EmailMessage
from django.conf import settings
from urllib.parse import urlencode
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import RFI, RFIVendorInvitation, RFIResponse
from tprm_backend.core.tenant_utils import get_tenant_id_from_request
from .email_templates import generate_rfi_rich_html_email
from ..input_sanitization import sanitize_invitation_custom_message

logger = logging.getLogger(__name__)


_RFI_SCRIPT_TAG_RE = re.compile(
    r"<\s*script[^>]*>.*?<\s*/\s*script\s*>",
    re.IGNORECASE | re.DOTALL,
)
_RFI_ONEVENT_ATTR_RE = re.compile(
    r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)",
    re.IGNORECASE,
)
_RFI_JS_URL_RE = re.compile(
    r"(href|src)\s*=\s*(\"javascript:[^\"]*\"|'javascript:[^']*'|javascript:[^\s>]*)",
    re.IGNORECASE,
)


def _sanitize_rfi_html_value(value):
    if not isinstance(value, str) or not value:
        return value

    sanitized = _RFI_SCRIPT_TAG_RE.sub("", value)
    sanitized = _RFI_ONEVENT_ATTR_RE.sub("", sanitized)
    sanitized = _RFI_JS_URL_RE.sub(r"\1=\"#\"", sanitized)
    return sanitized


def _sanitize_rfi_response_documents(documents):
    """
    Best-effort neutralization for any rich-text/HTML content in RFI response_documents.
    """
    if isinstance(documents, list):
        # If later you store rich HTML inside list items, extend this as needed.
        return documents

    if not isinstance(documents, dict):
        return documents

    sanitized = {}
    for key, value in documents.items():
        if isinstance(value, str) and "<" in value and ">" in value:
            sanitized[key] = _sanitize_rfi_html_value(value)
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_rfi_response_documents(value)
        else:
            sanitized[key] = value

    return sanitized


def _get_tenant_id(request):
    """Get tenant_id from authenticated user first, then fallback to request, default to 1 for development"""
    tenant_id = None
    user_id = None
    
    # PRIORITY 1: Get user_id from various sources
    if hasattr(request, 'user') and request.user:
        # Try multiple ways to get user_id
        user_id = (
            getattr(request.user, 'userid', None) or
            getattr(request.user, 'id', None) or
            getattr(request.user, 'UserId', None) or
            getattr(request.user, 'pk', None)
        )
    
    # If user_id not found from request.user, try JWT token
    if not user_id:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                import jwt
                from django.conf import settings
                token = auth_header.split(' ')[1]
                verification_key = getattr(settings, 'JWT_VERIFYING_KEY', None) or getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
                payload = jwt.decode(
                    token,
                    verification_key,
                    algorithms=getattr(settings, 'JWT_ALLOWED_ALGORITHMS', [getattr(settings, 'JWT_ALGORITHM', 'RS256')]),
                    issuer=getattr(settings, 'JWT_ISSUER', None),
                    audience=getattr(settings, 'JWT_AUDIENCE', None),
                )
                if payload:
                    user_id = payload.get('user_id') or payload.get('userid') or payload.get('id')
                    logger.info(f"[RFI Invitations] Extracted user_id {user_id} from JWT token")
            except Exception as jwt_error:
                logger.debug(f"[RFI Invitations] Error decoding JWT: {jwt_error}")
                pass
    
    # PRIORITY 2: Get tenant_id from users table using user_id
    if user_id:
        try:
            from django.db import connections
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                    SELECT TenantId
                    FROM users
                    WHERE UserId = %s
                    LIMIT 1
                """, [user_id])
                result = cursor.fetchone()
                if result and result[0]:
                    tenant_id = result[0]
                    logger.info(f"[RFI Invitations] Found tenant_id {tenant_id} from users table for user_id: {user_id}")
        except Exception as db_error:
            logger.debug(f"[RFI Invitations] Error querying users table: {db_error}")
            pass
    
    # PRIORITY 3: Try to get tenant_id from request.user object directly
    if not tenant_id and hasattr(request, 'user') and request.user:
        try:
            if hasattr(request.user, 'tenant_id'):
                tenant_id = request.user.tenant_id
            elif hasattr(request.user, 'tenant') and request.user.tenant:
                tenant_id = request.user.tenant.tenant_id
        except Exception as e:
            logger.debug(f"[RFI Invitations] Error getting tenant from user object: {e}")
            pass
    
    # PRIORITY 4: If not found from user, try request (might be set by middleware)
    if not tenant_id:
        tenant_id = get_tenant_id_from_request(request)
        if tenant_id:
            logger.warning(f"[RFI Invitations] Using tenant_id {tenant_id} from request (user_id={user_id})")
    
    # PRIORITY 5: If still no tenant_id, use default tenant (1) for development
    if not tenant_id:
        tenant_id = 1
        logger.warning(f"[RFI Invitations] No tenant found in user or request, using default tenant_id=1 for development (user_id={user_id})")
    
    return tenant_id


def _get_external_base_url():
    """Get external base URL for vendor portal links"""
    from django.conf import settings
    base = getattr(settings, 'EXTERNAL_BASE_URL', 'http://localhost:3000').rstrip('/')
    return base


@api_view(['POST'])
@permission_classes([AllowAny])
def generate_rfi_invitations(request):
    """
    Generate RFI vendor invitations and store in rfi_vendor_invitations.
    Expected payload: { rfiId, vendors: [{ vendor_id?, company_name, contact_email, contact_name?, vendor_phone? }], customMessage? }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        data = json.loads(request.body) if isinstance(request.body, bytes) else request.data
        rfi_id = data.get('rfiId')
        vendors = data.get('vendors', [])
        try:
            custom_message = sanitize_invitation_custom_message(
                data.get('customMessage', ''),
                field_name='customMessage'
            )
        except ValueError as validation_error:
            return JsonResponse({
                'success': False,
                'error': str(validation_error)
            }, status=400)

        logger.info(f"[RFI Invitations] Generating invitations for RFI {rfi_id}, {len(vendors)} vendors")

        if not rfi_id:
            return JsonResponse({'success': False, 'error': 'rfiId is required'}, status=400)
        if not vendors:
            return JsonResponse({'success': False, 'error': 'No vendors provided'}, status=400)

        tenant_id = _get_tenant_id(request)
        logger.info(f"[RFI Invitations] Using tenant_id={tenant_id}")

        try:
            rfi = RFI.objects.get(rfi_id=int(rfi_id), tenant_id=tenant_id)
            logger.info(f"[RFI Invitations] Found RFI: {rfi.rfi_number} - {rfi.rfi_title}")
        except RFI.DoesNotExist:
            logger.error(f"[RFI Invitations] RFI not found: rfi_id={rfi_id}, tenant_id={tenant_id}")
            return JsonResponse({'success': False, 'error': f'RFI not found: {rfi_id}'}, status=404)

        base_url = _get_external_base_url()
        created_invitations = []

        with transaction.atomic():
            for v in vendors:
                vendor_id = v.get('vendor_id') or v.get('vendorId')
                company_name = v.get('company_name') or v.get('companyName', '')
                contact_email = v.get('contact_email') or v.get('contactEmail') or v.get('email', '')
                contact_name = v.get('contact_name') or v.get('contactName') or v.get('vendor_name') or v.get('vendorName', '')
                contact_phone = v.get('contact_phone') or v.get('contactPhone') or v.get('vendor_phone') or v.get('vendorPhone', '')

                token = f"rfi-{secrets.token_urlsafe(24)}"
                submission_url = f"{base_url}/rfi-vendor-portal/{token}"

                existing = RFIVendorInvitation.objects.filter(
                    rfi_id=rfi_id,
                    vendor_email=contact_email
                ).first()

                if existing:
                    existing.invitation_url = submission_url
                    existing.submission_url = submission_url
                    existing.unique_token = token
                    existing.vendor_email = contact_email
                    existing.vendor_name = contact_name
                    existing.vendor_phone = contact_phone
                    existing.company_name = company_name
                    existing.custom_message = custom_message
                    existing.invitation_status = 'CREATED'
                    existing.save()
                    inv = existing
                else:
                    inv = RFIVendorInvitation.objects.create(
                        rfi=rfi,
                        tenant_id=tenant_id,
                        vendor_id=int(vendor_id) if vendor_id else None,
                        vendor_email=contact_email,
                        vendor_name=contact_name,
                        vendor_phone=contact_phone,
                        company_name=company_name,
                        invitation_url=submission_url,
                        submission_url=submission_url,
                        unique_token=token,
                        invitation_status='CREATED',
                        submission_source='invited',
                        custom_message=custom_message,
                    )

                created_invitations.append({
                    'invitation_id': inv.invitation_id,
                    'unique_token': inv.unique_token,
                    'invitation_url': inv.invitation_url,
                    'vendor_email': inv.vendor_email,
                    'company_name': inv.company_name,
                })

        logger.info(f"[RFI Invitations] Successfully created {len(created_invitations)} invitations")
        return JsonResponse({
            'success': True,
            'message': f'Generated {len(created_invitations)} invitation(s)',
            'invitations': created_invitations,
        })
    except json.JSONDecodeError as e:
        logger.error(f"[RFI Invitations] JSON decode error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        import traceback
        logger.error(f"[RFI Invitations] Error generating invitations: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': 'Failed to generate invitations',
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_rfi_invitation_by_token(request, token):
    """
    Get RFI details by invitation token (for vendor portal).
    Public endpoint - no auth required.
    """
    try:
        inv = RFIVendorInvitation.objects.filter(unique_token=token).select_related('rfi').first()
        if not inv:
            return JsonResponse({'success': False, 'error': 'Invalid or expired invitation'}, status=404)

        rfi = inv.rfi
        return JsonResponse({
            'success': True,
            'rfi': {
                'rfi_id': rfi.rfi_id,
                'rfi_number': rfi.rfi_number,
                'rfi_title': rfi.rfi_title,
                'description': getattr(rfi, 'description', '') or '',
                'submission_deadline': rfi.submission_deadline.isoformat() if rfi.submission_deadline else None,
                'estimated_value': str(rfi.estimated_value) if rfi.estimated_value else None,
            },
            'invitation': {
                'invitation_id': inv.invitation_id,
                'vendor_email': inv.vendor_email,
                'vendor_name': inv.vendor_name,
                'company_name': inv.company_name,
            },
        })
    except Exception as e:
        import traceback
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
@require_http_methods(["GET", "POST"])
def acknowledge_rfi_invitation(request, token):
    """
    Mark invitation as ACKNOWLEDGED and redirect to vendor portal
    This endpoint is called when vendor clicks the Acknowledge button in the email
    """
    from django.shortcuts import redirect
    from django.conf import settings
    
    try:
        inv = RFIVendorInvitation.objects.filter(unique_token=token).first()
        if not inv:
            # Redirect to error page
            external_base_url = getattr(settings, 'EXTERNAL_BASE_URL', 'http://localhost:3000').rstrip('/')
            return redirect(f"{external_base_url}/rfi-invitation-error?error=invalid_token")

        # Update invitation status
        inv.invitation_status = 'ACKNOWLEDGED'
        inv.acknowledged_date = timezone.now()
        inv.save()
        
        logger.info(f'[RFI ACKNOWLEDGE] Invitation {inv.invitation_id} acknowledged by {inv.vendor_email}')
        
        # Redirect without leaking token in query string.
        external_base_url = getattr(settings, 'EXTERNAL_BASE_URL', 'http://localhost:3000').rstrip('/')
        acknowledgment_page_url = f"{external_base_url}/rfi-invitation-acknowledged/{token}"
        
        return redirect(acknowledgment_page_url)
    except Exception as e:
        logger.error(f'[RFI ACKNOWLEDGE ERROR] {str(e)}')
        external_base_url = getattr(settings, 'EXTERNAL_BASE_URL', 'http://localhost:3000').rstrip('/')
        return redirect(f"{external_base_url}/rfi-invitation-error?error=server_error")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def decline_rfi_invitation(request, token):
    """
    Mark invitation as DECLINED and show confirmation page
    This endpoint is called when vendor clicks the Decline button in the email
    """
    from django.shortcuts import redirect
    from django.http import HttpResponse
    from django.conf import settings
    
    try:
        inv = RFIVendorInvitation.objects.filter(unique_token=token).first()
        if not inv:
            # Redirect to error page
            external_base_url = getattr(settings, 'EXTERNAL_BASE_URL', 'http://localhost:3000').rstrip('/')
            return redirect(f"{external_base_url}/rfi-invitation-error?error=invalid_token")

        # Get decline reason if provided (for POST requests)
        decline_reason = ''
        if request.method == 'POST':
            decline_reason = request.POST.get('reason', '')
        
        # Update invitation status
        inv.invitation_status = 'DECLINED'
        inv.declined_reason = decline_reason
        inv.acknowledged_date = timezone.now()  # Track when they declined
        inv.save()
        
        logger.info(f'[RFI DECLINE] Invitation {inv.invitation_id} declined by {inv.vendor_email}')
        
        # Redirect to decline confirmation page
        external_base_url = getattr(settings, 'EXTERNAL_BASE_URL', 'http://localhost:3000').rstrip('/')
        decline_confirmation_url = f"{external_base_url}/rfi-invitation-declined?vendor={inv.company_name}"
        
        return redirect(decline_confirmation_url)
    except Exception as e:
        logger.error(f'[RFI DECLINE ERROR] {str(e)}')
        external_base_url = getattr(settings, 'EXTERNAL_BASE_URL', 'http://localhost:3000').rstrip('/')
        return redirect(f"{external_base_url}/rfi-invitation-error?error=server_error")


@api_view(['POST'])
@permission_classes([AllowAny])
def create_rfi_response(request):
    """
    Create RFI response from vendor portal submission.
    Expected payload: { token, ...formData } or { invitationId, rfiId, ... }
    """
    try:
        data = request.data if hasattr(request, 'data') and request.data else json.loads(request.body)

        token = data.get('token')
        tenant_id = _get_tenant_id(request)

        invitation = None
        rfi = None

        if token:
            invitation = RFIVendorInvitation.objects.filter(unique_token=token).select_related('rfi').first()
            if invitation:
                rfi = invitation.rfi
                tenant_id = invitation.tenant_id or tenant_id

        if not rfi and data.get('rfiId'):
            try:
                rfi = RFI.objects.get(rfi_id=int(data['rfiId']), tenant_id=tenant_id)
            except RFI.DoesNotExist:
                pass

        if not rfi:
            return JsonResponse({'success': False, 'error': 'Invalid token or rfiId'}, status=400)

        # Build proposal_data from form fields
        proposal_data = {}
        for key in ['companyName', 'legalName', 'businessType', 'industrySector', 'contactName', 'contactTitle',
                    'contactEmail', 'contactPhone', 'website', 'taxId', 'dunsNumber', 'incorporationDate',
                    'employeeCount', 'annualRevenue', 'headquartersAddress', 'headquartersCountry',
                    'yearsInBusiness', 'companyDescription',
                    'demosTrialVersion', 'trialDuration', 'poc', 'differentiators', 'technologyStack',
                    'integrationCapabilities', 'trainingOptions', 'postImplementationSupport',
                    'updateFrequency', 'preferredCommunication',
                    'riskManagementPractices', 'disasterRecoveryBackup', 'complianceCertifications',
                    'legalTerms', 'termsAndConditions', 'nda', 'licensingTerms', 'exitStrategy']:
            if key in data and data[key] is not None:
                proposal_data[key] = data[key]

        org = data.get('companyName') or data.get('org', '')
        vendor_name = data.get('contactName') or data.get('vendorName', '')
        contact_email = data.get('contactEmail', '')
        contact_phone = data.get('contactPhone', '')

        with transaction.atomic():
            safe_documents = _sanitize_rfi_response_documents(data.get('documents', []))

            resp = RFIResponse.objects.create(
                rfi=rfi,
                tenant_id=tenant_id,
                vendor_id=invitation.vendor_id if invitation else None,
                invitation_id=invitation.invitation_id if invitation else None,
                org=org,
                vendor_name=vendor_name,
                contact_email=contact_email,
                contact_phone=contact_phone,
                proposal_data=proposal_data,
                response_documents=safe_documents,
                completion_percentage=data.get('completionPercentage'),
                submission_status='SUBMITTED',
                evaluation_status='SUBMITTED',
                submitted_at=timezone.now(),
                submission_source='invited' if invitation else 'open',
            )

            if invitation:
                invitation.invitation_status = 'SUBMITTED'
                invitation.save(update_fields=['invitation_status', 'updated_at'])

        return JsonResponse({
            'success': True,
            'response_id': resp.response_id,
            'message': 'RFI response submitted successfully',
        })
    except json.JSONDecodeError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': 'Failed to submit RFI response',
        }, status=500)


def _serialize_rfi_response(resp):
    """Serialize a single RFIResponse for list/detail API."""
    from django.utils.dateformat import format as date_format
    rfi = getattr(resp, 'rfi', None)
    return {
        'response_id': resp.response_id,
        'rfi_id': resp.rfi_id,
        'rfi_title': rfi.rfi_title if rfi else None,
        'rfi_number': rfi.rfi_number if rfi else None,
        'vendor_id': resp.vendor_id,
        'invitation_id': resp.invitation_id,
        'submission_date': resp.submission_date.isoformat() if resp.submission_date else None,
        'response_documents': resp.response_documents,
        'document_urls': resp.document_urls,
        'proposed_value': str(resp.proposed_value) if resp.proposed_value is not None else None,
        'technical_score': str(resp.technical_score) if resp.technical_score is not None else None,
        'commercial_score': str(resp.commercial_score) if resp.commercial_score is not None else None,
        'overall_score': str(resp.overall_score) if resp.overall_score is not None else None,
        'weighted_final_score': str(resp.weighted_final_score) if resp.weighted_final_score is not None else None,
        'evaluation_status': resp.evaluation_status,
        'auto_rejected': bool(resp.auto_rejected),
        'rejection_reason': resp.rejection_reason,
        'submission_source': resp.submission_source,
        'external_submission_data': resp.external_submission_data,
        'draft_data': resp.draft_data,
        'completion_percentage': str(resp.completion_percentage) if resp.completion_percentage is not None else None,
        'last_saved_at': resp.last_saved_at.isoformat() if resp.last_saved_at else None,
        'submitted_by': resp.submitted_by,
        'evaluated_by': resp.evaluated_by,
        'evaluation_date': resp.evaluation_date.isoformat() if resp.evaluation_date else None,
        'evaluation_comments': resp.evaluation_comments,
        'org': resp.org,
        'vendor_name': resp.vendor_name,
        'contact_email': resp.contact_email,
        'contact_phone': resp.contact_phone,
        'proposal_data': resp.proposal_data,
        'submission_status': resp.submission_status,
        'submitted_at': resp.submitted_at.isoformat() if resp.submitted_at else None,
        'ip_address': resp.ip_address,
        'created_at': resp.created_at.isoformat() if resp.created_at else None,
        'updated_at': resp.updated_at.isoformat() if resp.updated_at else None,
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def get_rfi_response_detail(request, response_id):
    """
    Get detailed RFI response by response_id.
    """
    tenant_id = _get_tenant_id(request)
    
    try:
        response_id_int = int(response_id)
    except ValueError:
        return Response({'error': 'Invalid response_id'}, status=400)
    
    try:
        if tenant_id:
            resp = RFIResponse.objects.filter(response_id=response_id_int, tenant_id=tenant_id).select_related('rfi').first()
        else:
            resp = RFIResponse.objects.filter(response_id=response_id_int).select_related('rfi').first()
        
        if not resp:
            return Response({'error': 'RFI response not found'}, status=404)
        
        data = _serialize_rfi_response(resp)
        return Response(data)
    except Exception as e:
        logger.error(f"[get_rfi_response_detail] Error: {str(e)}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_rfi_responses(request):
    """
    List RFI responses with optional filters.
    Query params: rfi_id, evaluation_status, submission_status, vendor_search
    """
    tenant_id = _get_tenant_id(request)
    print(f"[list_rfi_responses] Request received. Tenant ID: {tenant_id}")
    print(f"[list_rfi_responses] Query params: {request.query_params}")
    
    # Filter by tenant, but if tenant_id is None/0, show all (for development)
    if tenant_id:
        qs = RFIResponse.objects.filter(tenant_id=tenant_id).select_related('rfi').order_by('-created_at')
    else:
        # For development: if no tenant, show all responses
        qs = RFIResponse.objects.all().select_related('rfi').order_by('-created_at')
    
    print(f"[list_rfi_responses] Initial queryset count: {qs.count()}")

    rfi_id = request.query_params.get('rfi_id')
    if rfi_id:
        try:
            qs = qs.filter(rfi_id=int(rfi_id))
        except ValueError:
            pass

    evaluation_status = request.query_params.get('evaluation_status', '').strip()
    if evaluation_status:
        qs = qs.filter(evaluation_status=evaluation_status)

    submission_status = request.query_params.get('submission_status', '').strip()
    if submission_status:
        qs = qs.filter(submission_status=submission_status)

    vendor_search = request.query_params.get('vendor_search', '').strip()
    if vendor_search:
        from django.db.models import Q
        qs = qs.filter(
            Q(vendor_name__icontains=vendor_search) |
            Q(org__icontains=vendor_search) |
            Q(contact_email__icontains=vendor_search)
        )

    data = [_serialize_rfi_response(r) for r in qs]
    print(f"[list_rfi_responses] Serialized {len(data)} RFI responses")
    print(f"[list_rfi_responses] Sample response data (first item):", data[0] if data else "No data")
    return Response({'results': data})


@api_view(['POST'])
@permission_classes([AllowAny])
def send_rfi_invitation_emails(request):
    """
    Send RFI invitation emails to vendors
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return JsonResponse({'error': 'Tenant context not found'}, status=403)
    
    try:
        data = json.loads(request.body)
        invitations = data.get('invitations', [])
        rfi_data = data.get('rfiData', {})
        
        logger.info(f'[RFI EMAIL] Sending invitation emails for {len(invitations)} invitations')
        
        sent_emails = []
        failed_emails = []
        
        for invitation in invitations:
            try:
                # Update invitation status to SENT
                # MULTI-TENANCY: Filter by tenant
                invitation_obj = RFIVendorInvitation.objects.get(
                    invitation_id=invitation['invitation_id'],
                    tenant_id=tenant_id
                )
                invitation_obj.invitation_status = 'SENT'
                invitation_obj.invited_date = timezone.now()
                invitation_obj.save()
                
                # Prepare invitation data with unique_token for email template
                invitation_with_token = {
                    **invitation,
                    'unique_token': invitation_obj.unique_token
                }
                
                # Generate rich HTML email content
                email_data = {
                    'to': invitation['vendor_email'],
                    'subject': f"RFI Invitation: {rfi_data.get('rfi_title', 'Untitled RFI')}",
                    'body': generate_rfi_rich_html_email(invitation_with_token, rfi_data),
                    'invitation_url': invitation['invitation_url']
                }
                
                # Send actual email using Django's email system
                try:
                    email_message = EmailMessage(
                        subject=email_data['subject'],
                        body=email_data['body'],
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[invitation['vendor_email']],
                    )
                    email_message.content_subtype = "html"  # Set content type to HTML
                    
                    # Send the email - this will use our AzureADEmailBackend
                    result = email_message.send()
                    
                    logger.info(f'[RFI EMAIL SUCCESS] Email sent successfully to {invitation["vendor_email"]}')
                    
                except Exception as email_error:
                    logger.error(f'[RFI EMAIL ERROR] Failed to send email to {invitation["vendor_email"]}: {email_error}')
                    
                    # Continue with other invitations even if one fails
                    failed_emails.append({
                        'invitation_id': invitation['invitation_id'],
                        'vendor_email': invitation['vendor_email'],
                        'error': str(email_error),
                        'error_type': type(email_error).__name__
                    })
                    continue
                
                sent_emails.append({
                    'invitation_id': invitation['invitation_id'],
                    'vendor_email': invitation['vendor_email'],
                    'status': 'sent'
                })
                
            except Exception as e:
                logger.error(f'[RFI EMAIL ERROR] Failed to send email to {invitation.get("vendor_email", "unknown")}: {e}')
                failed_emails.append({
                    'invitation_id': invitation.get('invitation_id'),
                    'vendor_email': invitation.get('vendor_email'),
                    'error': str(e)
                })
        
        return JsonResponse({
            'success': True,
            'message': f'Sent {len(sent_emails)} emails successfully',
            'sent_emails': sent_emails,
            'failed_emails': failed_emails
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f'[RFI EMAIL ERROR] Error in send_rfi_invitation_emails: {e}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
