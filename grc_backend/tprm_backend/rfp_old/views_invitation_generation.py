"""
Views for generating vendor invitations using the new URI method
"""
import json
import time
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction, connection
from django.utils import timezone
from urllib.parse import urlencode
from rest_framework.decorators import api_view, authentication_classes, permission_classes

from .models import RFP, VendorInvitation, Vendor, RFPUnmatchedVendor
from .email_templates import generate_rich_html_email
from .rfp_authentication import JWTAuthentication, SimpleAuthenticatedPermission
from rbac.tprm_decorators import rbac_rfp_required


def generate_tracking_urls(rfp_id: int, invitation_id: int):
    """Generate acknowledge/decline tracking URLs that include rfp_id and invitation_id."""
    from django.conf import settings
    import re
    
    # Get backend URL and ensure it uses localhost (not ngrok)
    backend_url = getattr(settings, 'BACKEND_API_URL', 'http://localhost:8000').rstrip('/')
    
    # Replace any ngrok URLs with localhost:8000
    if 'ngrok' in backend_url.lower():
        backend_url = 'http://localhost:8000'
    
    # Ensure it's localhost (not 127.0.0.1 or other variations)
    if not backend_url.startswith('http://localhost') and not backend_url.startswith('https://localhost'):
        # Extract port if present, otherwise use 8000
        port_match = re.search(r':(\d+)', backend_url)
        port = port_match.group(1) if port_match else '8000'
        backend_url = f'http://localhost:{port}'
    
    # Point to API endpoints that record the status
    acknowledge_url = f"{backend_url}/api/v1/vendor-invitations/ack/{rfp_id}/{invitation_id}/"
    decline_url = f"{backend_url}/api/v1/vendor-invitations/decline/{rfp_id}/{invitation_id}/"
    return acknowledge_url, decline_url


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('create_rfp')
def generate_invitations_new_format(request):
    """
    Generate invitations using the new URI method with query parameters
    """
    try:
        data = json.loads(request.body)
        rfp_id = data.get('rfpId')
        vendors = data.get('vendors', [])
        custom_message = data.get('customMessage', '')
        
        if not rfp_id:
            return JsonResponse({
                'success': False,
                'error': 'RFP ID is required'
            }, status=400)
        
        if not vendors:
            return JsonResponse({
                'success': False,
                'error': 'No vendors provided'
            }, status=400)
        
        # Get RFP
        try:
            rfp = RFP.objects.get(rfp_id=rfp_id)
        except RFP.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'RFP not found: {rfp_id}'
            }, status=404)
        
        created_invitations = []
        
        print(f'[DEBUG] generate_invitations_new_format called with:')
        print(f'  rfp_id: {rfp_id}')
        print(f'  vendors: {vendors}')
        print(f'  custom_message: {custom_message}')
        
        with transaction.atomic():
            for vendor_data in vendors:
                print(f'[DEBUG] Processing vendor_data: {vendor_data}')
                # Generate new-style URL with query parameters
                # Strictly use http://localhost:3000 for vendor access portal
                from django.conf import settings
                import re
                
                # Get external base URL and ensure it uses localhost (not ngrok)
                external_base_url = getattr(settings, 'EXTERNAL_BASE_URL', 'http://localhost:3000').rstrip('/')
                
                # Replace any ngrok URLs with localhost:3000 (frontend port)
                if 'ngrok' in external_base_url.lower():
                    external_base_url = 'http://localhost:3000'
                
                # Ensure it's localhost (not 127.0.0.1 or other variations)
                if not external_base_url.startswith('http://localhost') and not external_base_url.startswith('https://localhost'):
                    # Extract port if present, otherwise use 3000
                    port_match = re.search(r':(\d+)', external_base_url)
                    port = port_match.group(1) if port_match else '3000'
                    external_base_url = f'http://localhost:{port}'
                
                base_url = f"{external_base_url}/submit"
                if 'localhost' in base_url or '127.0.0.1' in base_url or 'ngrok' in base_url.lower():
                    base_url = 'http://localhost:3000'
                base_url = f"{base_url}/submit"
                
                # Prepare parameters
                vendor_id = vendor_data.get('vendor_id')
                
                # Get primary contact information if this is a matched vendor
                contact_data = None
                if vendor_id:
                    with connection.cursor() as cursor:
                        cursor.execute('''
                            SELECT first_name, last_name, email, phone, mobile
                            FROM vendor_contacts
                            WHERE vendor_id = %s AND contact_type = 'PRIMARY' AND is_primary = 1 AND is_active = 1
                            LIMIT 1
                        ''', [vendor_id])
                        contact = cursor.fetchone()
                        if contact:
                            contact_data = {
                                'name': f'{contact[0]} {contact[1]}'.strip(),
                                'email': contact[2],
                                'phone': contact[3] or contact[4]  # Use mobile if phone is empty
                            }
                
                # Use contact data if available, otherwise fall back to vendor data
                params = {
                    'rfpId': str(rfp_id),
                    'vendorId': str(vendor_id) if vendor_id is not None else '',
                    'org': vendor_data.get('company_name', ''),
                    'vendorName': contact_data['name'] if contact_data else vendor_data.get('vendor_name', ''),
                    'contactEmail': contact_data['email'] if contact_data else vendor_data.get('email', ''),
                    'contactPhone': contact_data['phone'] if contact_data else vendor_data.get('phone', '')
                }
                
                print(f'[DEBUG] Backend processing vendor:')
                print(f'  vendor_id: {vendor_id} (type: {type(vendor_id)})')
                print(f'  vendor_name: {vendor_data.get("vendor_name", "")}')
                print(f'  email: {vendor_data.get("email", "")}')
                print(f'  company_name: {vendor_data.get("company_name", "")}')
                print(f'  params: {params}')
                
                # Remove empty parameters
                params = {k: v for k, v in params.items() if v}
                invitation_url = f"{base_url}?{urlencode(params)}"
                
                # Check if invitation already exists
                existing_invitation = None
                if vendor_data.get('vendor_id'):
                    try:
                        # Avoid ORM fetch of Vendor which can fail if table columns are out-of-sync
                        existing_invitation = VendorInvitation.objects.get(
                            rfp_id=rfp_id,
                            vendor_id=vendor_data.get('vendor_id')
                        )
                        print(f'[DEBUG] Found existing invitation for vendor {vendor_data.get("vendor_id")}, updating...')
                    except VendorInvitation.DoesNotExist:
                        pass
                
                if existing_invitation:
                    # Update existing invitation
                    existing_invitation.vendor_email = vendor_data.get('email', existing_invitation.vendor_email)
                    existing_invitation.vendor_name = vendor_data.get('vendor_name', existing_invitation.vendor_name)
                    existing_invitation.vendor_phone = vendor_data.get('phone', existing_invitation.vendor_phone)
                    existing_invitation.company_name = vendor_data.get('company_name', existing_invitation.company_name)
                    existing_invitation.invitation_url = invitation_url
                    existing_invitation.unique_token = f"INV{rfp_id}{vendor_data.get('vendor_id', '')}{int(time.time())}"
                    existing_invitation.custom_message = custom_message
                    existing_invitation.invitation_status = 'CREATED'  # Reset status for resending
                    existing_invitation.save()
                    invitation = existing_invitation
                    
                    # Generate tracking URLs for existing invitation
                    ack_url, decline_url = generate_tracking_urls(rfp_id, invitation.invitation_id)
                    invitation.acknowledgment_url = ack_url
                    invitation.save(update_fields=['acknowledgment_url'])
                else:
                    # Create new invitation record
                    # Assign by vendor_id to avoid querying Vendor ORM (works even if Vendor table is out-of-sync)
                    invitation = VendorInvitation.objects.create(
                        rfp_id=rfp_id,
                        vendor_id=vendor_data.get('vendor_id') or None,
                        vendor_email=vendor_data.get('email', ''),
                        vendor_name=vendor_data.get('vendor_name', ''),
                        vendor_phone=vendor_data.get('phone', ''),
                        company_name=vendor_data.get('company_name', ''),
                        invitation_url=invitation_url,
                        unique_token=f"INV{rfp_id}{vendor_data.get('vendor_id', '')}{int(time.time())}",
                        is_matched_vendor=vendor_data.get('is_matched_vendor', False),
                        submission_source='invited',
                        invitation_status='CREATED',
                        custom_message=custom_message,
                        utm_parameters={
                            'utm_source': 'rfp_portal',
                            'utm_medium': 'email',
                            'utm_campaign': 'vendor_invitation',
                            'utm_content': f'rfp_{rfp_id}'
                        }
                    )
                    
                    # Generate tracking URLs for new invitation
                    ack_url, decline_url = generate_tracking_urls(rfp_id, invitation.invitation_id)
                    invitation.acknowledgment_url = ack_url
                    invitation.save(update_fields=['acknowledgment_url'])
                
                created_invitations.append({
                    'invitation_id': invitation.invitation_id,
                    'vendor_name': invitation.vendor_name,
                    'vendor_email': invitation.vendor_email,
                    'company_name': invitation.company_name,
                    'invitation_url': invitation.invitation_url,
                    'acknowledgment_url': invitation.acknowledgment_url,
                    'decline_url': decline_url,
                    'unique_token': invitation.unique_token,
                    'is_matched_vendor': invitation.is_matched_vendor
                })
        
        return JsonResponse({
            'success': True,
            'message': f'Generated {len(created_invitations)} invitation(s) successfully',
            'invitations': created_invitations
        })
        
    except json.JSONDecodeError as e:
        error_msg = f'Invalid JSON data: {str(e)}'
        print(f'[ERROR] {error_msg}')
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': error_msg
        }, status=400)
    except Exception as e:
        error_msg = f'Failed to generate invitations: {str(e)}'
        print(f'[ERROR] {error_msg}')
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': error_msg
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('create_rfp')
def generate_open_rfp_invitation(request):
    """
    Generate invitation for open RFP (no specific vendor)
    """
    try:
        data = json.loads(request.body)
        rfp_id = data.get('rfpId')
        
        if not rfp_id:
            return JsonResponse({
                'success': False,
                'error': 'RFP ID is required'
            }, status=400)
        
        # Get RFP
        try:
            rfp = RFP.objects.get(rfp_id=rfp_id)
        except RFP.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'RFP not found: {rfp_id}'
            }, status=404)
        
        # Generate open RFP URL
        # Strictly use http://localhost:3000 for vendor access portal
        from django.conf import settings
        import re
        
        # Get external base URL and ensure it uses localhost (not ngrok)
        external_base_url = getattr(settings, 'EXTERNAL_BASE_URL', 'http://localhost:3000').rstrip('/')
        
        # Replace any ngrok URLs with localhost:3000 (frontend port)
        if 'ngrok' in external_base_url.lower():
            external_base_url = 'http://localhost:3000'
        
        # Ensure it's localhost (not 127.0.0.1 or other variations)
        if not external_base_url.startswith('http://localhost') and not external_base_url.startswith('https://localhost'):
            # Extract port if present, otherwise use 3000
            port_match = re.search(r':(\d+)', external_base_url)
            port = port_match.group(1) if port_match else '3000'
            external_base_url = f'http://localhost:{port}'
        
        base_url = f"{external_base_url}/submit/open"
        if 'localhost' in base_url or '127.0.0.1' in base_url or 'ngrok' in base_url.lower():
            base_url = 'http://localhost:3000'
        base_url = f"{base_url}/submit/open"
        params = {
            'rfpId': str(rfp_id)
        }
        invitation_url = f"{base_url}?{urlencode(params)}"
        
        # Create invitation record for open RFP
        invitation = VendorInvitation.objects.create(
            rfp_id=rfp_id,
            vendor=None,  # Use vendor field instead of vendor_id
            vendor_email='',
            vendor_name='',
            vendor_phone='',
            company_name='',
            invitation_url=invitation_url,
            unique_token=f"OPEN{rfp_id}{int(time.time())}",
            is_matched_vendor=False,
            submission_source='open',
            invitation_status='CREATED',
            custom_message='',
            utm_parameters={
                'utm_source': 'rfp_portal',
                'utm_medium': 'public',
                'utm_campaign': 'open_rfp',
                'utm_content': f'open_rfp_{rfp_id}'
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Open RFP invitation generated successfully',
            'invitation': {
                'invitation_id': invitation.invitation_id,
                'invitation_url': invitation.invitation_url,
                'unique_token': invitation.unique_token,
                'is_matched_vendor': False
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to generate open RFP invitation: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_invitations_by_rfp(request, rfp_id):
    """
    Get all invitations for a specific RFP
    """
    try:
        invitations = VendorInvitation.objects.filter(rfp_id=rfp_id).order_by('-created_at')
        
        invitation_list = []
        for invitation in invitations:
            invitation_list.append({
                'invitation_id': invitation.invitation_id,
                'vendor_name': invitation.vendor_name,
                'vendor_email': invitation.vendor_email,
                'company_name': invitation.company_name,
                'vendor_phone': invitation.vendor_phone,
                'invitation_url': invitation.invitation_url,
                'unique_token': invitation.unique_token,
                'invitation_status': invitation.invitation_status,
                'invited_date': invitation.invited_date.isoformat() if invitation.invited_date else None,
                'acknowledged_date': invitation.acknowledged_date.isoformat() if invitation.acknowledged_date else None,
                'declined_reason': invitation.declined_reason,
                'is_matched_vendor': invitation.is_matched_vendor,
                'submission_source': invitation.submission_source,
                'custom_message': invitation.custom_message,
                'created_at': invitation.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'invitations': invitation_list,
            'total': len(invitation_list)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to fetch invitations: {str(e)}'
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('create_rfp')
def send_invitation_emails(request):
    """
    Send invitation emails to vendors
    """
    try:
        data = json.loads(request.body)
        invitations = data.get('invitations', [])
        rfp_data = data.get('rfpData', {})
        
        print(f'[EMAIL] Sending invitation emails for {len(invitations)} invitations')
        
        sent_emails = []
        failed_emails = []
        
        for invitation in invitations:
            try:
                # Update invitation status to SENT
                invitation_obj = VendorInvitation.objects.get(invitation_id=invitation['invitation_id'])
                invitation_obj.invitation_status = 'SENT'
                invitation_obj.invited_date = timezone.now()
                invitation_obj.save()
                
                # Generate rich HTML email content
                email_data = {
                    'to': invitation['vendor_email'],
                    'subject': f"RFP Invitation: {rfp_data.get('rfp_title', 'Untitled RFP')}",
                    'body': generate_rich_html_email(invitation, rfp_data),
                    'invitation_url': invitation['invitation_url'],
                    'acknowledgment_url': invitation.get('acknowledgment_url', invitation['invitation_url']),
                    'decline_url': invitation.get('decline_url', f"{invitation['invitation_url']}?action=decline")
                }
                
                # Send actual email using Django's email system
                from django.core.mail import EmailMessage
                from django.conf import settings
                
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
                    
                    print(f'[SUCCESS] Email sent successfully to {invitation["vendor_email"]}')
                    
                except Exception as email_error:
                    print(f'[ERROR] Failed to send email to {invitation["vendor_email"]}: {email_error}')
                    
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
                print(f'[DEBUG ERROR] Failed to send email to {invitation.get("vendor_email", "unknown")}: {e}')
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
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

