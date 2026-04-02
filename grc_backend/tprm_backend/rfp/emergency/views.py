from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.db import transaction
from .models import EmergencyProcurement, EmergencyEvaluationCriteria
from .serializers import EmergencyProcurementSerializer, EmergencyProcurementCreateSerializer, EmergencyProcurementListSerializer, EmergencyEvaluationCriteriaSerializer
from tprm_backend.core.tenant_utils import get_tenant_id_from_request

def _get_or_create_dev_superuser():
    """
    Development fallback user bootstrap made race-safe for concurrent requests.
    """
    from django.contrib.auth.models import User

    existing_superuser = User.objects.filter(is_superuser=True).order_by('id').first()
    if existing_superuser:
        return existing_superuser

    try:
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@example.com',
                    'is_superuser': True,
                    'is_staff': True,
                    'is_active': True,
                },
            )
            if created:
                user.set_password('admin123')
                user.save(update_fields=['password'])
            elif not user.is_superuser or not user.is_staff:
                user.is_superuser = True
                user.is_staff = True
                user.save(update_fields=['is_superuser', 'is_staff'])
            return user
    except Exception:
        return User.objects.filter(is_superuser=True).order_by('id').first() or User.objects.get(username='admin')


class EmergencyProcurementViewSet(viewsets.ModelViewSet):
    """API endpoint for managing Emergency Procurements"""
    queryset = EmergencyProcurement.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['emergency_title', 'description', 'emergency_number']
    ordering_fields = ['created_at', 'updated_at', 'submission_deadline', 'emergency_title']
    ordering = ['-created_at']
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'list':
            return EmergencyProcurementListSerializer
        elif self.action == 'create':
            return EmergencyProcurementCreateSerializer
        return EmergencyProcurementSerializer
    
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
        
        admin_user = _get_or_create_dev_superuser()
        
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
            print(f"Exception during Emergency Procurement creation: {str(e)}")
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
            # If Emergency Procurement doesn't exist, create it instead (upsert behavior)
            # This handles the case where frontend has stale ID in localStorage
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"[Emergency Procurement Update] Emergency Procurement with ID {pk} not found. Creating new Emergency Procurement instead (upsert).")
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
            print(f"Exception during Emergency Procurement update: {str(e)}")
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class EmergencyEvaluationCriteriaViewSet(viewsets.ModelViewSet):
    """API endpoint for managing Emergency Procurement evaluation criteria"""
    queryset = EmergencyEvaluationCriteria.objects.all()
    serializer_class = EmergencyEvaluationCriteriaSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        emergency_id = self.request.query_params.get('emergency_id', None)
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
        
        if emergency_id:
            queryset = queryset.filter(emergency_id=emergency_id)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        return queryset
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to handle bulk delete by emergency_id"""
        emergency_id = request.query_params.get('emergency_id', None)
        if emergency_id and not kwargs.get('pk'):
            queryset = self.get_queryset().filter(emergency_id=emergency_id)
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
        
        admin_user = _get_or_create_dev_superuser()
        
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
            logger.error(f"Exception during Emergency Procurement evaluation criteria creation: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class EmergencyTypeView(APIView):
    """API endpoint for getting Emergency Procurement types"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get list of unique Emergency Procurement types from existing Emergency Procurements"""
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
        
        queryset = EmergencyProcurement.objects.all()
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        emergency_types = queryset.values_list('emergency_type', flat=True).distinct().order_by('emergency_type')
        return Response({
            'success': True,
            'emergency_types': list(emergency_types)
        })
