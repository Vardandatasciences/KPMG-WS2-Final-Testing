"""
Views for compliance app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.conf import settings
import jwt
import logging
from .models import Framework, ComplianceMapping
from .serializers import (
    FrameworkSerializer, ComplianceMappingSerializer, ComplianceMappingDetailSerializer
)

logger = logging.getLogger(__name__)


class SimpleAuthenticatedPermission(BasePermission):
    """Custom permission class that checks for authenticated users"""
    def has_permission(self, request, view):
        # Check if user is authenticated
        return bool(
            request.user and 
            hasattr(request.user, 'userid') and
            getattr(request.user, 'is_authenticated', False)
        )


class JWTAuthentication(BaseAuthentication):
    """Custom JWT authentication class for DRF"""
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        try:
            token = auth_header.split(' ')[1]
            # Use JWT_SECRET_KEY from settings
            secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            if user_id:
                try:
                    from mfa_auth.models import User
                    user = User.objects.get(userid=user_id)
                    # Add is_authenticated attribute for DRF compatibility
                    user.is_authenticated = True
                    return (user, token)
                except (User.DoesNotExist, ImportError):
                    # If User model doesn't exist or user not found, create a mock user
                    class MockUser:
                        def __init__(self, user_id):
                            self.userid = user_id
                            self.username = f"user_{user_id}"
                            self.is_authenticated = True
                    
                    return (MockUser(user_id), token)
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
        except Exception as e:
            logger.error(f"JWT authentication error: {str(e)}")
            return None


class FrameworkViewSet(viewsets.ModelViewSet):
    """ViewSet for Framework model."""
    queryset = Framework.objects.all()
    serializer_class = FrameworkSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['Category', 'Status', 'ActiveInactive', 'InternalExternal']
    search_fields = ['FrameworkName', 'FrameworkDescription', 'Category']
    ordering_fields = ['FrameworkName', 'CurrentVersion', 'EffectiveDate']
    ordering = ['FrameworkName']

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active frameworks."""
        active_frameworks = self.queryset.filter(ActiveInactive='Active')
        serializer = self.get_serializer(active_frameworks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get frameworks grouped by category."""
        category = request.query_params.get('category')
        if category:
            frameworks = self.queryset.filter(Category=category)
        else:
            frameworks = self.queryset.all()
        
        # Group by category
        categories = {}
        for framework in frameworks:
            if framework.Category not in categories:
                categories[framework.Category] = []
            categories[framework.Category].append(
                self.get_serializer(framework).data
            )
        
        return Response(categories)


class ComplianceMappingViewSet(viewsets.ModelViewSet):
    """ViewSet for ComplianceMapping model."""
    queryset = ComplianceMapping.objects.all()
    serializer_class = ComplianceMappingSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['sla_id', 'framework_id', 'compliance_status', 'audit_frequency']
    search_fields = ['compliance_description', 'assigned_auditor']
    ordering_fields = ['compliance_score', 'last_audited', 'next_audit_due']
    ordering = ['-compliance_score']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ComplianceMappingDetailSerializer
        return ComplianceMappingSerializer

    @action(detail=False, methods=['get'])
    def by_sla(self, request):
        """Get compliance mappings for a specific SLA"""
        sla_id = request.query_params.get('sla_id')
        if not sla_id:
            return Response({'error': 'sla_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        mappings = self.queryset.filter(sla_id=sla_id)
        serializer = self.get_serializer(mappings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_framework(self, request):
        """Get compliance mappings for a specific framework"""
        framework_id = request.query_params.get('framework_id')
        if not framework_id:
            return Response({'error': 'framework_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        mappings = self.queryset.filter(framework_id=framework_id)
        serializer = self.get_serializer(mappings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get compliance mapping summary statistics"""
        from django.db.models import Avg
        
        total_mappings = self.queryset.count()
        compliant_mappings = self.queryset.filter(compliance_status='Compliant').count()
        avg_compliance_score = self.queryset.aggregate(
            avg_score=Avg('compliance_score')
        )['avg_score'] or 0
        
        return Response({
            'total_mappings': total_mappings,
            'compliant_mappings': compliant_mappings,
            'non_compliant_mappings': total_mappings - compliant_mappings,
            'average_compliance_score': round(float(avg_compliance_score), 2),
            'compliance_rate': round((compliant_mappings / total_mappings * 100) if total_mappings > 0 else 0, 2)
        })