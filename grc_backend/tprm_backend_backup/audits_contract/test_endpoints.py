"""
Test endpoints for debugging audit findings creation.
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import ContractAudit, ContractAuditFinding
from .serializers import ContractAuditFindingSerializer


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def test_database_connection(request):
    """Test database connection and table existence."""
    try:
        from django.db import connections
        
        # Test basic model operations
        total_audits = ContractAudit.objects.count()
        total_findings = ContractAuditFinding.objects.count()
        
        # Test raw SQL to check table existence
        with connections['default'].cursor() as cursor:
            # Check if contract_audit_findings table exists
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'contract_audit_findings'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            # Get table structure if it exists
            table_structure = []
            if table_exists:
                cursor.execute("DESCRIBE contract_audit_findings")
                table_structure = cursor.fetchall()
        
        return Response({
            'success': True,
            'database_connection': 'OK',
            'total_audits': total_audits,
            'total_findings': total_findings,
            'contract_audit_findings_table_exists': table_exists,
            'table_structure': table_structure,
            'database_name': connections['default'].settings_dict['NAME']
        })
        
    except Exception as e:
        import traceback
        return Response({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def test_create_finding(request):
    """Test endpoint to create a sample audit finding."""
    try:
        print(f"🧪 Testing audit finding creation with data: {request.data}")
        
        # Create a test finding
        finding_data = {
            'audit_id': request.data.get('audit_id', 1),
            'term_id': request.data.get('term_id', 'test_term_1'),
            'evidence': request.data.get('evidence', 'Test evidence'),
            'user_id': request.data.get('user_id', 1),
            'how_to_verify': request.data.get('how_to_verify', 'Test verification method'),
            'impact_recommendations': request.data.get('impact_recommendations', 'Test recommendations'),
            'details_of_finding': request.data.get('details_of_finding', 'Test finding details'),
            'comment': request.data.get('comment', 'Test comment'),
            'check_date': request.data.get('check_date', '2024-01-01'),
            'questionnaire_responses': request.data.get('questionnaire_responses', '{}')
        }
        
        print(f"🧪 Creating test finding with data: {finding_data}")
        
        # Use the serializer to create the finding
        serializer = ContractAuditFindingSerializer(data=finding_data)
        if serializer.is_valid():
            finding = serializer.save()
            print(f"✅ Test finding created successfully with ID: {finding.finding_id}")
            return Response({
                'success': True,
                'data': ContractAuditFindingSerializer(finding).data,
                'message': 'Test audit finding created successfully'
            }, status=status.HTTP_201_CREATED)
        else:
            print(f"❌ Serializer validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        print(f"❌ Error in test endpoint: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': str(e),
            'details': 'Failed to create test finding'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
