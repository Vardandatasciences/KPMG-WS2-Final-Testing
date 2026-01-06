from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import RFP
from .document_generator import generate_rfp_document
from .rfp_authentication import JWTAuthentication, SimpleAuthenticatedPermission
from rbac.tprm_decorators import rbac_rfp_required
import json


@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def generate_rfp_word_document(request, rfp_id):
    """
    Generate and download RFP as Word document
    """
    try:
        rfp = get_object_or_404(RFP, rfp_id=rfp_id)
        
        # Convert RFP model to dictionary
        rfp_data = {
            'rfp_id': rfp.rfp_id,
            'rfp_number': rfp.rfp_number,
            'rfp_title': rfp.rfp_title,
            'description': rfp.description,
            'rfp_type': rfp.rfp_type,
            'category': rfp.category,
            'estimated_value': float(rfp.estimated_value) if rfp.estimated_value else None,
            'currency': rfp.currency,
            'budget_range_min': float(rfp.budget_range_min) if rfp.budget_range_min else None,
            'budget_range_max': float(rfp.budget_range_max) if rfp.budget_range_max else None,
            'issue_date': rfp.issue_date.isoformat() if rfp.issue_date else None,
            'submission_deadline': rfp.submission_deadline.isoformat() if rfp.submission_deadline else None,
            'evaluation_period_end': rfp.evaluation_period_end.isoformat() if rfp.evaluation_period_end else None,
            'evaluation_method': rfp.evaluation_method,
            'criticality_level': rfp.criticality_level,
            'geographical_scope': rfp.geographical_scope,
            'compliance_requirements': rfp.compliance_requirements,
            'allow_late_submissions': rfp.allow_late_submissions,
            'auto_approved': rfp.auto_approved,
            'status': rfp.status,
            'evaluation_criteria': []
        }
        
        # Add evaluation criteria if they exist
        try:
            # Check if evaluation_criteria is a JSON field or RelatedManager
            if hasattr(rfp, 'evaluation_criteria'):
                if isinstance(rfp.evaluation_criteria, str):
                    # It's a JSON string field
                    criteria_data = json.loads(rfp.evaluation_criteria)
                    rfp_data['evaluation_criteria'] = criteria_data
                else:
                    # It's a RelatedManager, convert to list
                    criteria_list = []
                    for criteria in rfp.evaluation_criteria.all():
                        criteria_list.append({
                            'criteria_name': getattr(criteria, 'criteria_name', 'N/A'),
                            'weight_percentage': getattr(criteria, 'weight_percentage', 0),
                            'criteria_description': getattr(criteria, 'criteria_description', 'N/A'),
                            'veto_enabled': getattr(criteria, 'veto_enabled', False)
                        })
                    rfp_data['evaluation_criteria'] = criteria_list
            else:
                rfp_data['evaluation_criteria'] = []
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            print(f"Warning: Could not process evaluation criteria: {e}")
            rfp_data['evaluation_criteria'] = []
        
        # Generate Word document
        return generate_rfp_document(rfp_data, 'word')
        
    except Exception as e:
        return HttpResponse(
            f'Failed to generate Word document: {str(e)}',
            status=500,
            content_type='text/plain'
        )


@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def generate_rfp_pdf_document(request, rfp_id):
    """
    Generate and download RFP as PDF document
    """
    try:
        rfp = get_object_or_404(RFP, rfp_id=rfp_id)
        
        # Convert RFP model to dictionary
        rfp_data = {
            'rfp_id': rfp.rfp_id,
            'rfp_number': rfp.rfp_number,
            'rfp_title': rfp.rfp_title,
            'description': rfp.description,
            'rfp_type': rfp.rfp_type,
            'category': rfp.category,
            'estimated_value': float(rfp.estimated_value) if rfp.estimated_value else None,
            'currency': rfp.currency,
            'budget_range_min': float(rfp.budget_range_min) if rfp.budget_range_min else None,
            'budget_range_max': float(rfp.budget_range_max) if rfp.budget_range_max else None,
            'issue_date': rfp.issue_date.isoformat() if rfp.issue_date else None,
            'submission_deadline': rfp.submission_deadline.isoformat() if rfp.submission_deadline else None,
            'evaluation_period_end': rfp.evaluation_period_end.isoformat() if rfp.evaluation_period_end else None,
            'evaluation_method': rfp.evaluation_method,
            'criticality_level': rfp.criticality_level,
            'geographical_scope': rfp.geographical_scope,
            'compliance_requirements': rfp.compliance_requirements,
            'allow_late_submissions': rfp.allow_late_submissions,
            'auto_approved': rfp.auto_approved,
            'status': rfp.status,
            'evaluation_criteria': []
        }
        
        # Add evaluation criteria if they exist
        try:
            # Check if evaluation_criteria is a JSON field or RelatedManager
            if hasattr(rfp, 'evaluation_criteria'):
                if isinstance(rfp.evaluation_criteria, str):
                    # It's a JSON string field
                    criteria_data = json.loads(rfp.evaluation_criteria)
                    rfp_data['evaluation_criteria'] = criteria_data
                else:
                    # It's a RelatedManager, convert to list
                    criteria_list = []
                    for criteria in rfp.evaluation_criteria.all():
                        criteria_list.append({
                            'criteria_name': getattr(criteria, 'criteria_name', 'N/A'),
                            'weight_percentage': getattr(criteria, 'weight_percentage', 0),
                            'criteria_description': getattr(criteria, 'criteria_description', 'N/A'),
                            'veto_enabled': getattr(criteria, 'veto_enabled', False)
                        })
                    rfp_data['evaluation_criteria'] = criteria_list
            else:
                rfp_data['evaluation_criteria'] = []
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            print(f"Warning: Could not process evaluation criteria: {e}")
            rfp_data['evaluation_criteria'] = []
        
        # Generate PDF document
        return generate_rfp_document(rfp_data, 'pdf')
        
    except Exception as e:
        return HttpResponse(
            f'Failed to generate PDF document: {str(e)}',
            status=500,
            content_type='text/plain'
        )


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('create_rfp')
def generate_document_from_data(request):
    """
    Generate document from provided RFP data (for preview before saving)
    """
    try:
        print(f"Document generation request received: {request.method}")
        print(f"Request data keys: {list(request.data.keys())}")
        rfp_data = request.data
        
        # Validate required fields
        required_fields = ['rfp_number', 'rfp_title', 'description', 'rfp_type']
        for field in required_fields:
            if not rfp_data.get(field):
                return Response(
                    {'error': f'Missing required field: {field}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        format_type = request.data.get('format', 'word').lower()
        if format_type not in ['word', 'pdf']:
            return Response(
                {'error': 'Format must be "word" or "pdf"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate document
        return generate_rfp_document(rfp_data, format_type)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to generate document: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def preview_rfp_document(request, rfp_id):
    """
    Preview RFP document in browser (PDF only)
    """
    try:
        rfp = get_object_or_404(RFP, rfp_id=rfp_id)
        
        # Convert RFP model to dictionary
        rfp_data = {
            'rfp_id': rfp.rfp_id,
            'rfp_number': rfp.rfp_number,
            'rfp_title': rfp.rfp_title,
            'description': rfp.description,
            'rfp_type': rfp.rfp_type,
            'category': rfp.category,
            'estimated_value': float(rfp.estimated_value) if rfp.estimated_value else None,
            'currency': rfp.currency,
            'budget_range_min': float(rfp.budget_range_min) if rfp.budget_range_min else None,
            'budget_range_max': float(rfp.budget_range_max) if rfp.budget_range_max else None,
            'issue_date': rfp.issue_date.isoformat() if rfp.issue_date else None,
            'submission_deadline': rfp.submission_deadline.isoformat() if rfp.submission_deadline else None,
            'evaluation_period_end': rfp.evaluation_period_end.isoformat() if rfp.evaluation_period_end else None,
            'evaluation_method': rfp.evaluation_method,
            'criticality_level': rfp.criticality_level,
            'geographical_scope': rfp.geographical_scope,
            'compliance_requirements': rfp.compliance_requirements,
            'allow_late_submissions': rfp.allow_late_submissions,
            'auto_approved': rfp.auto_approved,
            'status': rfp.status,
            'evaluation_criteria': []
        }
        
        # Add evaluation criteria if they exist
        if hasattr(rfp, 'evaluation_criteria') and rfp.evaluation_criteria:
            try:
                criteria_data = json.loads(rfp.evaluation_criteria) if isinstance(rfp.evaluation_criteria, str) else rfp.evaluation_criteria
                rfp_data['evaluation_criteria'] = criteria_data
            except (json.JSONDecodeError, TypeError):
                rfp_data['evaluation_criteria'] = []
        
        # Generate PDF for preview
        generator = RFPDocumentGenerator(rfp_data)
        pdf_buffer = generator.generate_pdf_document()
        
        response = HttpResponse(
            pdf_buffer.getvalue(),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = 'inline; filename="rfp_preview.pdf"'
        
        return response
        
    except Exception as e:
        return Response(
            {'error': f'Failed to generate preview: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
