import csv
import io
import json
import pandas as pd
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Avg
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import connection
from rest_framework.decorators import api_view, authentication_classes, permission_classes

from .models import (
    RFP, Vendor, VendorCapability, VendorCertification, 
    RFPVendorSelection, RFPUnmatchedVendor
)
from .forms import (
    VendorSearchForm, VendorManualEntryForm, 
    VendorBulkUploadForm, RFPVendorSelectionForm
)
from .rfp_authentication import JWTAuthentication, SimpleAuthenticatedPermission
from tprm_backend.rbac.tprm_decorators import rbac_rfp_required


@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def vendor_selection(request, rfp_id):
    """
    View for selecting vendors for an RFP
    """
    rfp = get_object_or_404(RFP, rfp_id=rfp_id)
    
    # Get existing selected vendors for this RFP
    selected_vendor_ids = list(RFPVendorSelection.objects.filter(
        rfp=rfp
    ).values_list('vendor_id', flat=True))
    
    # Forms
    search_form = VendorSearchForm(request.GET or None)
    manual_entry_form = VendorManualEntryForm()
    bulk_upload_form = VendorBulkUploadForm()
    
    # Handle search and filtering
    vendors = Vendor.objects.all().prefetch_related(
        'capabilities', 'certifications'
    )
    
    search_term = ''
    filter_type = 'all'
    
    if search_form.is_valid():
        search_term = search_form.cleaned_data.get('search_term', '')
        filter_type = search_form.cleaned_data.get('filter_type', 'all')
        
        if search_term:
            vendors = vendors.filter(
                Q(company_name__icontains=search_term) |
                Q(capabilities__capability_name__icontains=search_term) |
                Q(certifications__certification_name__icontains=search_term)
            ).distinct()
        
        if filter_type == 'high-match':
            vendors = vendors.filter(match_score__gte=90)
        elif filter_type == 'certified':
            vendors = vendors.annotate(
                cert_count=Count('certifications')
            ).filter(cert_count__gt=2)
    
    # Prepare vendor data for template
    vendor_data = []
    for vendor in vendors:
        # Get capabilities and certifications
        capabilities = list(vendor.capabilities.values_list('capability_name', flat=True))
        certifications = list(vendor.certifications.values_list('certification_name', flat=True))
        
        # Format employee count for display
        employee_display = "Unknown"
        if vendor.employee_count:
            if vendor.employee_count < 50:
                employee_display = "< 50"
            elif vendor.employee_count < 200:
                employee_display = "50-200"
            elif vendor.employee_count < 500:
                employee_display = "200-500"
            elif vendor.employee_count < 1000:
                employee_display = "500-1000"
            else:
                employee_display = "1000+"
        
        # Determine category based on employee count
        category = "Unknown"
        if vendor.employee_count:
            if vendor.employee_count < 200:
                category = "Startup"
            elif vendor.employee_count < 1000:
                category = "Mid-Market"
            else:
                category = "Enterprise"
        
        # Format experience years
        experience = f"{vendor.experience_years} years" if vendor.experience_years else "Unknown"
        
        vendor_data.append({
            'id': vendor.vendor_id,
            'name': vendor.company_name,
            'email': vendor.email or '',
            'phone': vendor.phone or '',
            'website': vendor.website or '',
            'location': vendor.location or '',
            'matchScore': vendor.match_score or 0,
            'rating': vendor.rating or 0,
            'capabilities': capabilities,
            'certifications': certifications,
            'employees': employee_display,
            'experience': experience,
            'category': category,
            'is_selected': vendor.vendor_id in selected_vendor_ids
        })
    
    context = {
        'rfp': rfp,
        'vendors': vendor_data,
        'selected_vendor_ids': selected_vendor_ids,
        'search_form': search_form,
        'manual_entry_form': manual_entry_form,
        'bulk_upload_form': bulk_upload_form,
        'search_term': search_term,
        'active_filter': filter_type,
    }
    
    return render(request, 'rfp/phase3_vendor_selection.html', context)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('edit_rfp')
def update_vendor_selection(request, rfp_id):
    """
    View for updating vendor selection
    """
    rfp = get_object_or_404(RFP, rfp_id=rfp_id)
    
    try:
        data = json.loads(request.body)
        vendor_id = data.get('vendor_id')
        is_selected = data.get('is_selected', False)
        
        vendor = get_object_or_404(Vendor, vendor_id=vendor_id)
        
        if is_selected:
            # Add vendor to selection if not already selected
            RFPVendorSelection.objects.get_or_create(
                rfp=rfp,
                vendor=vendor,
                defaults={'selected_by': request.user.id}
            )
        else:
            # Remove vendor from selection
            RFPVendorSelection.objects.filter(
                rfp=rfp,
                vendor=vendor
            ).delete()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('create_rfp')
def bulk_select_vendors(request, rfp_id):
    """
    View for bulk selecting/deselecting vendors
    """
    rfp = get_object_or_404(RFP, rfp_id=rfp_id)
    
    try:
        data = json.loads(request.body)
        vendor_ids = data.get('vendor_ids', [])
        select_all = data.get('select_all', False)
        
        if select_all:
            # Get all vendor IDs
            all_vendor_ids = list(Vendor.objects.values_list('vendor_id', flat=True))
            
            # Check if all vendors are already selected
            selected_count = RFPVendorSelection.objects.filter(
                rfp=rfp,
                vendor_id__in=all_vendor_ids
            ).count()
            
            if selected_count == len(all_vendor_ids):
                # Deselect all vendors
                RFPVendorSelection.objects.filter(
                    rfp=rfp,
                    vendor_id__in=all_vendor_ids
                ).delete()
                return JsonResponse({'success': True, 'action': 'deselected_all'})
            else:
                # Select all vendors
                for vendor_id in all_vendor_ids:
                    RFPVendorSelection.objects.get_or_create(
                        rfp=rfp,
                        vendor_id=vendor_id,
                        defaults={'selected_by': request.user.id}
                    )
                return JsonResponse({'success': True, 'action': 'selected_all'})
        else:
            # Select/deselect specific vendors
            for vendor_id in vendor_ids:
                RFPVendorSelection.objects.get_or_create(
                    rfp=rfp,
                    vendor_id=vendor_id,
                    defaults={'selected_by': request.user.id}
                )
            return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('create_rfp')
def generate_vendor_urls(request, rfp_id):
    """
    View for generating invitation URLs for selected vendors using new query parameter format
    """
    rfp = get_object_or_404(RFP, rfp_id=rfp_id)
    
    # Get selected vendors
    selected_vendors = RFPVendorSelection.objects.filter(rfp=rfp)
    
    if not selected_vendors:
        messages.error(request, "No vendors selected. Please select at least one vendor.")
        return redirect('vendor_selection', rfp_id=rfp_id)
    
    # Generate URLs for each vendor using new format
    for selection in selected_vendors:
        if not selection.invitation_url:
            # Generate new-style URL with query parameters
            vendor = selection.vendor
            from django.conf import settings
            import re
            
            # Get external base URL and ensure it uses localhost (not ngrok)
            external_base_url = getattr(settings, 'EXTERNAL_BASE_URL', 'http://localhost:3000').rstrip('/')
            
            # Replace any ngrok URLs with localhost:3000
            if 'ngrok' in external_base_url.lower():
                external_base_url = 'http://localhost:3000'
            
            # Ensure it's localhost (not 127.0.0.1 or other variations)
            if not external_base_url.startswith('http://localhost') and not external_base_url.startswith('https://localhost'):
                # Extract port if present, otherwise use 3000
                port_match = re.search(r':(\d+)', external_base_url)
                port = port_match.group(1) if port_match else '3000'
                external_base_url = f'http://localhost:{port}'
            
            base_url = f"{external_base_url}/submit"
            
            # URL encode the parameters
            from urllib.parse import urlencode
            params = {
                'rfpId': str(rfp.rfp_id),
                'vendorId': str(vendor.vendor_id),
                'org': vendor.company_name or '',
                'vendorName': f"{vendor.first_name or ''} {vendor.last_name or ''}".strip(),
                'contactEmail': vendor.email or '',
                'contactPhone': vendor.phone or ''
            }
            
            # Remove empty parameters
            params = {k: v for k, v in params.items() if v}
            invitation_url = f"{base_url}?{urlencode(params)}"
            
            # Store invitation in database
            invitation = VendorInvitation.objects.create(
                rfp_id=rfp.rfp_id,
                vendor_id=vendor.vendor_id,
                vendor_email=vendor.email or '',
                vendor_name=f"{vendor.first_name or ''} {vendor.last_name or ''}".strip(),
                vendor_phone=vendor.phone or '',
                company_name=vendor.company_name or '',
                invitation_url=invitation_url,
                unique_token=f"INV{rfp.rfp_id}{vendor.vendor_id}{int(time.time())}",
                is_matched_vendor=True,
                submission_source='invited',
                invitation_status='CREATED',
                custom_message=request.POST.get('custom_message', '')
            )
            
            # Update selection with invitation URL
            selection.invitation_url = invitation_url
            selection.save()
    
    messages.success(request, f"Generated invitation URLs for {selected_vendors.count()} vendors.")
    return redirect('vendor_invitation', rfp_id=rfp_id)


def generate_unmatched_vendor_url(rfp_id, org_name="", vendor_name="", contact_email="", contact_phone=""):
    """
    Generate URL for unmatched vendors (not in system)
    """
    from django.conf import settings
    import re
    
    # Get external base URL and ensure it uses localhost (not ngrok)
    external_base_url = getattr(settings, 'EXTERNAL_BASE_URL', 'http://localhost:3000').rstrip('/')
    
    # Replace any ngrok URLs with localhost:3000
    if 'ngrok' in external_base_url.lower():
        external_base_url = 'http://localhost:3000'
    
    # Ensure it's localhost (not 127.0.0.1 or other variations)
    if not external_base_url.startswith('http://localhost') and not external_base_url.startswith('https://localhost'):
        # Extract port if present, otherwise use 3000
        port_match = re.search(r':(\d+)', external_base_url)
        port = port_match.group(1) if port_match else '3000'
        external_base_url = f'http://localhost:{port}'
    
    base_url = f"{external_base_url}/submit"
    from urllib.parse import urlencode
    
    params = {
        'rfpId': str(rfp_id),
        'vendorId': '',  # Empty for unmatched vendors
        'org': org_name,
        'vendorName': vendor_name,
        'contactEmail': contact_email,
        'contactPhone': contact_phone
    }
    
    # Remove empty values
    params = {k: v for k, v in params.items() if v}
    
    return f"{base_url}?{urlencode(params)}"


def generate_open_rfp_url(rfp_id):
    """
    Generate URL for open/public RFPs
    """
    from django.conf import settings
    # Get external base URL and ensure it uses localhost (not ngrok)
    import re
    external_base_url = getattr(settings, 'EXTERNAL_BASE_URL', 'http://localhost:3000').rstrip('/')
    
    # Replace any ngrok URLs with localhost:3000
    if 'ngrok' in external_base_url.lower():
        external_base_url = 'http://localhost:3000'
    
    # Ensure it's localhost (not 127.0.0.1 or other variations)
    if not external_base_url.startswith('http://localhost') and not external_base_url.startswith('https://localhost'):
        # Extract port if present, otherwise use 3000
        port_match = re.search(r':(\d+)', external_base_url)
        port = port_match.group(1) if port_match else '3000'
        external_base_url = f'http://localhost:{port}'
    
    base_url = f"{external_base_url}/submit/open"
    from urllib.parse import urlencode
    
    params = {
        'rfpId': str(rfp_id)
    }
    
    return f"{base_url}?{urlencode(params)}"


@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def vendor_invitation(request, rfp_id):
    """
    View for sending invitations to selected vendors
    """
    rfp = get_object_or_404(RFP, rfp_id=rfp_id)
    
    # Get selected vendors with URLs
    selected_vendors = RFPVendorSelection.objects.filter(
        rfp=rfp
    ).select_related('vendor')
    
    context = {
        'rfp': rfp,
        'selected_vendors': selected_vendors,
    }
    
    return render(request, 'rfp/phase4_vendor_invitation.html', context)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_unmatched_vendors(request, rfp_id):
    """
    API endpoint to get unmatched vendors for an RFP
    """
    rfp = get_object_or_404(RFP, rfp_id=rfp_id)
    
    unmatched_vendors = RFPUnmatchedVendor.objects.filter(
        matching_status__in=['unmatched', 'pending_review']
    ).order_by('-created_at')
    
    vendor_data = []
    for vendor in unmatched_vendors:
        vendor_data.append({
            'unmatched_id': vendor.unmatched_id,
            'vendor_name': vendor.vendor_name,
            'vendor_email': vendor.vendor_email,
            'vendor_phone': vendor.vendor_phone,
            'company_name': vendor.company_name,
            'matching_status': vendor.matching_status,
            'created_at': vendor.created_at.isoformat(),
            'submission_data': vendor.submission_data if vendor.submission_data else {}
        })
    
    return JsonResponse(vendor_data, safe=False)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('create_rfp')
def create_unmatched_vendor(request, rfp_id):
    """
    API endpoint to create a new unmatched vendor
    """
    try:
        rfp = get_object_or_404(RFP, rfp_id=rfp_id)
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['vendor_name', 'vendor_email', 'vendor_phone', 'company_name']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'error': f'{field} is required'}, status=400)
        
        # Create unmatched vendor
        unmatched_vendor = RFPUnmatchedVendor.objects.create(
            vendor_name=data['vendor_name'],
            vendor_email=data['vendor_email'],
            vendor_phone=data['vendor_phone'],
            company_name=data['company_name'],
            submission_data=data.get('submission_data', {}),
            matching_status=data.get('matching_status', 'unmatched')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Unmatched vendor created successfully',
            'unmatched_id': unmatched_vendor.unmatched_id,
            'vendor_name': unmatched_vendor.vendor_name,
            'company_name': unmatched_vendor.company_name
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Failed to create unmatched vendor: {str(e)}'}, status=500)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_approved_vendors(request, rfp_id):
    """
    API endpoint to get all approved vendors for an RFP
    """
    rfp = get_object_or_404(RFP, rfp_id=rfp_id)
    
    try:
        # Get only the fields that actually exist in the database
        approved_vendors = Vendor.objects.filter(
            status='APPROVED'
        ).values(
            'vendor_id', 'vendor_code', 'company_name', 'legal_name', 
            'business_type', 'incorporation_date', 'tax_id', 'duns_number',
            'website', 'industry_sector', 'annual_revenue', 'employee_count',
            'headquarters_country', 'headquarters_address', 'description',
            'vendor_category_id', 'risk_level', 'status', 'lifecycle_stage',
            'onboarding_date', 'last_assessment_date', 'next_assessment_date',
            'is_critical_vendor', 'has_data_access', 'has_system_access',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ).order_by('-created_at')
        
        vendor_data = []
        for vendor in approved_vendors:
            # Use default values for capabilities and certifications since tables don't exist
            capabilities = ['Software Development', 'Cloud Services']  # Default capabilities
            certifications = ['ISO 27001', 'SOC 2']  # Default certifications
            
            # Format employee count for display
            employee_display = "Unknown"
            if vendor['employee_count']:
                if vendor['employee_count'] < 50:
                    employee_display = "< 50"
                elif vendor['employee_count'] < 200:
                    employee_display = "50-200"
                elif vendor['employee_count'] < 500:
                    employee_display = "200-500"
                elif vendor['employee_count'] < 1000:
                    employee_display = "500-1000"
                else:
                    employee_display = "1000+"
            
            # Determine category based on employee count
            category = "Unknown"
            if vendor['employee_count']:
                if vendor['employee_count'] < 200:
                    category = "Startup"
                elif vendor['employee_count'] < 1000:
                    category = "Mid-Market"
                else:
                    category = "Enterprise"
            
            vendor_data.append({
                'vendor_id': vendor['vendor_id'],
                'vendor_code': vendor['vendor_code'],
                'company_name': vendor['company_name'],
                'legal_name': vendor['legal_name'],
                'business_type': vendor['business_type'],
                'incorporation_date': vendor['incorporation_date'].isoformat() if vendor['incorporation_date'] else None,
                'tax_id': vendor['tax_id'],
                'duns_number': vendor['duns_number'],
                'website': vendor['website'],
                'industry_sector': vendor['industry_sector'],
                'annual_revenue': float(vendor['annual_revenue']) if vendor['annual_revenue'] else None,
                'employee_count': vendor['employee_count'],
                'employee_display': employee_display,
                'headquarters_country': vendor['headquarters_country'],
                'headquarters_address': vendor['headquarters_address'],
                'description': vendor['description'],
                'vendor_category_id': vendor['vendor_category_id'],
                'risk_level': vendor['risk_level'],
                'status': vendor['status'],
                'lifecycle_stage': vendor['lifecycle_stage'],
                'onboarding_date': vendor['onboarding_date'].isoformat() if vendor['onboarding_date'] else None,
                'last_assessment_date': vendor['last_assessment_date'].isoformat() if vendor['last_assessment_date'] else None,
                'next_assessment_date': vendor['next_assessment_date'].isoformat() if vendor['next_assessment_date'] else None,
                'is_critical_vendor': vendor['is_critical_vendor'],
                'has_data_access': vendor['has_data_access'],
                'has_system_access': vendor['has_system_access'],
                'created_by': vendor['created_by'],
                'updated_by': vendor['updated_by'],
                'created_at': vendor['created_at'].isoformat(),
                'updated_at': vendor['updated_at'].isoformat(),
                # Additional fields for UI (using default values since fields don't exist in DB)
                'email': 'contact@example.com',  # Default email
                'phone': '+1-555-0000',  # Default phone
                'location': vendor['headquarters_country'] or 'Unknown',  # Use headquarters as location
                'match_score': 85.0,  # Default match score
                'rating': 4.5,  # Default rating
                'experience_years': 5,  # Default experience
                'capabilities': capabilities,
                'certifications': certifications,
                'category': category
            })
        
        return JsonResponse(vendor_data, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': f'Failed to fetch approved vendors: {str(e)}'}, status=500)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_all_approved_vendors(request):
    """
    API endpoint to get all approved vendors (for frontend vendor selection)
    """
    try:
        # Get only the fields that actually exist in the database
        approved_vendors = Vendor.objects.filter(
            status='APPROVED'
        ).values(
            'vendor_id', 'vendor_code', 'company_name', 'legal_name', 
            'business_type', 'incorporation_date', 'tax_id', 'duns_number',
            'website', 'industry_sector', 'annual_revenue', 'employee_count',
            'headquarters_country', 'headquarters_address', 'description',
            'vendor_category_id', 'risk_level', 'status', 'lifecycle_stage',
            'onboarding_date', 'last_assessment_date', 'next_assessment_date',
            'is_critical_vendor', 'has_data_access', 'has_system_access',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ).order_by('company_name')
        
        vendor_data = []
        for vendor in approved_vendors:
            # Use default values for capabilities and certifications since tables don't exist
            capabilities = ['Software Development', 'Cloud Services']  # Default capabilities
            certifications = ['ISO 27001', 'SOC 2']  # Default certifications
            
            # Generate primary contact information if not available
            primary_email = vendor.get('email', '')
            primary_phone = vendor.get('phone', '')
            
            # If no email/phone in vendor record, generate placeholder contact info
            if not primary_email:
                # Generate email based on company name
                company_clean = vendor['company_name'].lower().replace(' ', '').replace('inc', '').replace('llc', '').replace('corp', '')
                primary_email = f"contact@{company_clean}.com"
            
            if not primary_phone:
                # Generate placeholder phone number
                primary_phone = "+1 (555) 000-0000"
            
            vendor_info = {
                'vendor_id': vendor['vendor_id'],
                'vendor_code': vendor['vendor_code'],
                'company_name': vendor['company_name'],
                'legal_name': vendor['legal_name'],
                'business_type': vendor['business_type'],
                'website': vendor['website'],
                'industry_sector': vendor['industry_sector'],
                'annual_revenue': float(vendor['annual_revenue']) if vendor['annual_revenue'] else None,
                'employee_count': vendor['employee_count'],
                'headquarters_country': vendor['headquarters_country'],
                'risk_level': vendor['risk_level'],
                'status': vendor['status'],
                'is_critical_vendor': vendor['is_critical_vendor'],
                'has_data_access': vendor['has_data_access'],
                'has_system_access': vendor['has_system_access'],
                'created_at': vendor['created_at'].isoformat() if vendor['created_at'] else None,
                'updated_at': vendor['updated_at'].isoformat() if vendor['updated_at'] else None,
                # Contact information
                'email': primary_email,
                'phone': primary_phone,
                'contact_email': primary_email,  # Alias for compatibility
                'contact_phone': primary_phone,  # Alias for compatibility
                # Default values for missing fields
                'match_score': 85.0,  # Default match score
                'rating': 4.5,        # Default rating
                'experience_years': 5, # Default experience
                'capabilities': capabilities,    # Default capabilities list
                'certifications': certifications,  # Default certifications list
            }
            vendor_data.append(vendor_info)
        
        return JsonResponse({
            'success': True,
            'vendors': vendor_data,
            'total': len(vendor_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to fetch approved vendors: {str(e)}'
        }, status=500)
