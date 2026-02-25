from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from .models import DirectProcurement, DirectEvaluationCriteria
from .serializers import DirectProcurementSerializer, DirectProcurementCreateSerializer, DirectProcurementListSerializer, DirectEvaluationCriteriaSerializer
from tprm_backend.core.tenant_utils import get_tenant_id_from_request


class DirectProcurementViewSet(viewsets.ModelViewSet):
    """API endpoint for managing Direct Procurements"""
    queryset = DirectProcurement.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['direct_title', 'description', 'direct_number']
    ordering_fields = ['created_at', 'updated_at', 'submission_deadline', 'direct_title']
    ordering = ['-created_at']
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'list':
            return DirectProcurementListSerializer
        elif self.action == 'create':
            return DirectProcurementCreateSerializer
        return DirectProcurementSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        tenant_id = get_tenant_id_from_request(self.request)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Override create to handle tenant and user assignment"""
        tenant_id = get_tenant_id_from_request(request)
        
        # If tenant_id not found, try to get from user or use default for development
        if not tenant_id:
            # Try to get tenant from user
            if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
                try:
                    # Try to get tenant_id from user model
                    if hasattr(request.user, 'tenant_id'):
                        tenant_id = request.user.tenant_id
                    elif hasattr(request.user, 'tenant') and request.user.tenant:
                        tenant_id = request.user.tenant.tenant_id
                    elif hasattr(request.user, 'userid'):
                        # Query users table to get tenant_id
                        from django.db import connections
                        try:
                            with connections['default'].cursor() as cursor:
                                cursor.execute("""
                                    SELECT TenantId
                                    FROM users
                                    WHERE UserId = %s
                                    LIMIT 1
                                """, [request.user.userid])
                                result = cursor.fetchone()
                                if result and result[0]:
                                    tenant_id = result[0]
                        except Exception:
                            pass
                except Exception:
                    pass
            
            # If still no tenant_id, use default tenant (1) for development
            if not tenant_id:
                tenant_id = 1
        
        from django.contrib.auth.models import User
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin', email='admin@example.com', password='admin123'
            )
        
        data = request.data.copy() if hasattr(request.data, 'copy') else request.data
        if 'tenant_id' not in data:
            data['tenant_id'] = tenant_id
        
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
            # Save with created_by and tenant_id (these will override any values in validated_data)
            serializer.save(created_by=admin_user.id, tenant_id=tenant_id)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            import traceback
            print(f"Exception during Direct Procurement creation: {str(e)}")
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Override update to handle tenant and user assignment - supports upsert (create if not exists)"""
        from rest_framework.exceptions import NotFound
        partial = kwargs.pop('partial', False)
        pk = kwargs.get('pk') or self.kwargs.get('pk')
        
        try:
            instance = self.get_object()
        except NotFound:
            # If Direct Procurement doesn't exist, create it instead (upsert behavior)
            # This handles the case where frontend has stale ID in localStorage
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"[Direct Procurement Update] Direct Procurement with ID {pk} not found. Creating new Direct Procurement instead (upsert).")
            # Delegate to create method
            return self.create(request, *args, **kwargs)
        
        # Get tenant_id for the update
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            # Try to get tenant from user or use default for development
            if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
                try:
                    if hasattr(request.user, 'tenant_id'):
                        tenant_id = request.user.tenant_id
                    elif hasattr(request.user, 'tenant') and request.user.tenant:
                        tenant_id = request.user.tenant.tenant_id
                    elif hasattr(request.user, 'userid'):
                        from django.db import connections
                        try:
                            with connections['default'].cursor() as cursor:
                                cursor.execute("""
                                    SELECT TenantId
                                    FROM users
                                    WHERE UserId = %s
                                    LIMIT 1
                                """, [request.user.userid])
                                result = cursor.fetchone()
                                if result and result[0]:
                                    tenant_id = result[0]
                        except Exception:
                            pass
                except Exception:
                    pass
            
            # If still no tenant_id, use default tenant (1) for development
            if not tenant_id:
                tenant_id = 1
        
        data = request.data.copy() if hasattr(request.data, 'copy') else request.data
        if 'tenant_id' not in data:
            data['tenant_id'] = tenant_id
        
        serializer = self.get_serializer(instance, data=data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            print(f"Exception during Direct Procurement update: {str(e)}")
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DirectEvaluationCriteriaViewSet(viewsets.ModelViewSet):
    """API endpoint for managing Direct Procurement evaluation criteria"""
    queryset = DirectEvaluationCriteria.objects.all()
    serializer_class = DirectEvaluationCriteriaSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        direct_id = self.request.query_params.get('direct_id', None)
        tenant_id = get_tenant_id_from_request(self.request)
        
        # If tenant_id not found, try to get from user or use default for development
        if not tenant_id:
            if hasattr(self.request, 'user') and self.request.user and hasattr(self.request.user, 'is_authenticated') and self.request.user.is_authenticated:
                try:
                    if hasattr(self.request.user, 'tenant_id'):
                        tenant_id = self.request.user.tenant_id
                    elif hasattr(self.request.user, 'tenant') and self.request.user.tenant:
                        tenant_id = self.request.user.tenant.tenant_id
                    elif hasattr(self.request.user, 'userid'):
                        from django.db import connections
                        try:
                            with connections['default'].cursor() as cursor:
                                cursor.execute("""
                                    SELECT TenantId
                                    FROM users
                                    WHERE UserId = %s
                                    LIMIT 1
                                """, [self.request.user.userid])
                                result = cursor.fetchone()
                                if result and result[0]:
                                    tenant_id = result[0]
                        except Exception:
                            pass
                except Exception:
                    pass
            
            # If still no tenant_id, use default tenant (1) for development
            if not tenant_id:
                tenant_id = 1
        
        if direct_id:
            queryset = queryset.filter(direct_id=direct_id)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        return queryset
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to handle bulk delete by direct_id"""
        direct_id = request.query_params.get('direct_id', None)
        if direct_id and not kwargs.get('pk'):
            queryset = self.get_queryset().filter(direct_id=direct_id)
            count = queryset.count()
            queryset.delete()
            return Response({'deleted_count': count}, status=status.HTTP_204_NO_CONTENT)
        return super().destroy(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """Override create to handle tenant and user assignment"""
        tenant_id = get_tenant_id_from_request(request)
        
        # If tenant_id not found, try to get from user or use default for development
        if not tenant_id:
            if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
                try:
                    if hasattr(request.user, 'tenant_id'):
                        tenant_id = request.user.tenant_id
                    elif hasattr(request.user, 'tenant') and request.user.tenant:
                        tenant_id = request.user.tenant.tenant_id
                    elif hasattr(request.user, 'userid'):
                        from django.db import connections
                        try:
                            with connections['default'].cursor() as cursor:
                                cursor.execute("""
                                    SELECT TenantId
                                    FROM users
                                    WHERE UserId = %s
                                    LIMIT 1
                                """, [request.user.userid])
                                result = cursor.fetchone()
                                if result and result[0]:
                                    tenant_id = result[0]
                        except Exception:
                            pass
                except Exception:
                    pass
            
            # If still no tenant_id, use default tenant (1) for development
            if not tenant_id:
                tenant_id = 1
        
        from django.contrib.auth.models import User
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin', email='admin@example.com', password='admin123'
            )
        
        # Get user_id from request.user if available
        user_id = None
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            if hasattr(request.user, 'userid'):
                user_id = request.user.userid
            elif hasattr(request.user, 'id'):
                user_id = request.user.id
        
        data = request.data.copy() if hasattr(request.data, 'copy') else request.data
        if 'tenant_id' not in data:
            data['tenant_id'] = tenant_id
        
        # Add created_by to data before validation if not present
        if 'created_by' not in data or not data.get('created_by'):
            data['created_by'] = user_id if user_id else admin_user.id
        
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
            # Ensure created_by and tenant_id are set during save
            created_by_value = user_id if user_id else admin_user.id
            serializer.save(created_by=created_by_value, tenant_id=tenant_id)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Exception during Direct Procurement evaluation criteria creation: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DirectTypeView(APIView):
    """API endpoint for getting Direct Procurement types"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get list of unique Direct Procurement types from existing Direct Procurements"""
        tenant_id = get_tenant_id_from_request(request)
        
        # If tenant_id not found, try to get from user or use default for development
        if not tenant_id:
            if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
                try:
                    if hasattr(request.user, 'tenant_id'):
                        tenant_id = request.user.tenant_id
                    elif hasattr(request.user, 'tenant') and request.user.tenant:
                        tenant_id = request.user.tenant.tenant_id
                    elif hasattr(request.user, 'userid'):
                        from django.db import connections
                        try:
                            with connections['default'].cursor() as cursor:
                                cursor.execute("""
                                    SELECT TenantId
                                    FROM users
                                    WHERE UserId = %s
                                    LIMIT 1
                                """, [request.user.userid])
                                result = cursor.fetchone()
                                if result and result[0]:
                                    tenant_id = result[0]
                        except Exception:
                            pass
                except Exception:
                    pass
            
            # If still no tenant_id, use default tenant (1) for development
            if not tenant_id:
                tenant_id = 1
        
        queryset = DirectProcurement.objects.all()
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        direct_types = queryset.values_list('direct_type', flat=True).distinct().order_by('direct_type')
        return Response({
            'success': True,
            'direct_types': list(direct_types)
        })
