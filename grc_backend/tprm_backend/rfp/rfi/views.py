import logging
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
from .models import RFI, RFIEvaluationCriteria
from .serializers import RFISerializer, RFICreateSerializer, RFIListSerializer, RFIEvaluationCriteriaSerializer
from tprm_backend.core.tenant_utils import (
    get_tenant_id_from_request,
    filter_queryset_by_tenant,
    get_tenant_aware_queryset,
)

logger = logging.getLogger(__name__)

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


class RFIViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing RFIs
    """
    queryset = RFI.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['rfi_title', 'description', 'rfi_number']
    ordering_fields = ['created_at', 'updated_at', 'submission_deadline', 'rfi_title']
    ordering = ['-created_at']
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'list':
            return RFIListSerializer
        elif self.action == 'create':
            return RFICreateSerializer
        return RFISerializer
    
    def get_queryset(self):
        """Filter queryset by tenant, prioritize user's tenant_id over request"""
        queryset = super().get_queryset()
        tenant_id = None
        user_id = None
        
        # PRIORITY 1: Get user_id from various sources
        if hasattr(self.request, 'user') and self.request.user:
            # Try multiple ways to get user_id
            user_id = (
                getattr(self.request.user, 'userid', None) or
                getattr(self.request.user, 'id', None) or
                getattr(self.request.user, 'UserId', None) or
                getattr(self.request.user, 'pk', None)
            )
        
        # If user_id not found from request.user, try JWT token
        if not user_id:
            auth_header = self.request.headers.get('Authorization', '')
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
                        logger.info(f"[RFI List] Extracted user_id {user_id} from JWT token")
                except Exception as jwt_error:
                    logger.debug(f"[RFI List] Error decoding JWT: {jwt_error}")
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
                        logger.info(f"[RFI List] Found tenant_id {tenant_id} from users table for user_id: {user_id}")
            except Exception as db_error:
                logger.debug(f"[RFI List] Error querying users table: {db_error}")
                pass
        
        # PRIORITY 3: Try to get tenant_id from request.user object directly
        if not tenant_id and hasattr(self.request, 'user') and self.request.user:
            try:
                if hasattr(self.request.user, 'tenant_id'):
                    tenant_id = self.request.user.tenant_id
                elif hasattr(self.request.user, 'tenant') and self.request.user.tenant:
                    tenant_id = self.request.user.tenant.tenant_id
            except Exception as e:
                logger.debug(f"[RFI List] Error getting tenant from user object: {e}")
                pass
        
        # PRIORITY 4: If not found from user, try request (might be set by middleware)
        if not tenant_id:
            tenant_id = get_tenant_id_from_request(self.request)
            if tenant_id:
                logger.warning(f"[RFI List] Using tenant_id {tenant_id} from request (user_id={user_id})")
        
        # Only filter by tenant if tenant_id is found
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
            logger.info(f"[RFI List] Filtering RFIs for tenant_id={tenant_id} (user_id={user_id})")
        else:
            # For development, if no tenant is found, don't filter (allow all)
            logger.warning(f"[RFI List] No tenant found in user or request, showing all RFIs (user_id={user_id})")
        
        return queryset
    
    def get_object(self):
        """Override get_object to handle tenant filtering more gracefully"""
        # Get the pk from URL (DRF uses 'pk' as default URL kwarg)
        pk = self.kwargs.get('pk')
        if not pk:
            raise NotFound("RFI ID not provided in URL.")
        
        queryset = self.get_queryset()
        
        # Try to get the object from the filtered queryset first
        try:
            obj = queryset.get(rfi_id=pk)
            return obj
        except RFI.DoesNotExist:
            # If not found in filtered queryset, try without tenant filter (for development)
            tenant_id = get_tenant_id_from_request(self.request)
            if not tenant_id:
                # For development, try to get the object without tenant filter
                try:
                    obj = RFI.objects.get(rfi_id=pk)
                    return obj
                except RFI.DoesNotExist:
                    pass
            # Re-raise the original exception
            raise NotFound(f"RFI with rfi_id={pk} not found.")
    
    def list(self, request, *args, **kwargs):
        """Override list to handle tenant filtering"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            tenant_id = get_tenant_id_from_request(request)
            logger.info(f"[RFI List] Fetching RFIs for tenant_id={tenant_id}")
            
            queryset = self.filter_queryset(self.get_queryset())
            logger.info(f"[RFI List] Found {queryset.count()} RFIs")
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            import traceback
            logger.error(f"[RFI List] Error fetching RFIs: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({
                'error': str(e),
                'detail': 'An error occurred while fetching RFIs'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve an RFI
        If auto_approve is True, set status to APPROVED directly without requiring approval workflow
        """
        rfi = self.get_object()
        
        # Get user_id from request.user if available
        user_id = None
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            if hasattr(request.user, 'userid'):
                user_id = request.user.userid
            elif hasattr(request.user, 'id'):
                user_id = request.user.id
            elif hasattr(request.user, 'UserId'):
                user_id = request.user.UserId
        
        # Default to 1 if no user found
        approved_by = user_id if user_id else 1
        
        # If auto_approve is enabled, allow approval from any status (except CANCELLED/ARCHIVED)
        if rfi.auto_approve:
            if rfi.status in ['CANCELLED', 'ARCHIVED']:
                return Response(
                    {"error": "Cannot approve a cancelled or archived RFI"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Directly approve without requiring IN_REVIEW status
            rfi.status = 'APPROVED'
            rfi.approved_by = approved_by
            rfi.approval_workflow_id = None  # No approval workflow needed for auto-approve
            rfi.save()
            return Response({
                "status": "RFI auto-approved",
                "message": "RFI has been automatically approved without approval workflow",
                "rfi_id": rfi.rfi_id,
                "rfi_number": rfi.rfi_number,
                "rfi_title": rfi.rfi_title
            })
        
        # For non-auto-approve RFIs, require IN_REVIEW status
        if rfi.status != 'IN_REVIEW':
            return Response(
                {"error": "Only RFIs in IN_REVIEW status can be approved"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Enforce maker–checker: creator cannot approve their own RFI
        try:
            creator_id_int = int(rfi.created_by) if rfi.created_by is not None else None
            current_user_id_int = int(approved_by) if approved_by is not None else None
        except (TypeError, ValueError):
            logger.warning("[RFI Approve] Invalid creator or approver id while approving RFI")
            return Response(
                {"error": "Invalid approver id. Please contact an administrator."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if creator_id_int is not None and current_user_id_int is not None and creator_id_int == current_user_id_int:
            logger.warning(f"[RFI Approve] Self-approval attempt detected for RFI ID {rfi.rfi_id} by user {creator_id_int}")
            return Response(
                {"error": "Self-approval is not allowed. Please assign a different reviewer to approve this RFI."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update status to APPROVED for normal approval workflow (after all stages approved)
        rfi.status = 'APPROVED'
        rfi.approved_by = current_user_id_int if current_user_id_int is not None else approved_by
        rfi.save()
        
        return Response({
            "status": "RFI approved",
            "message": "RFI has been approved",
            "rfi_id": rfi.rfi_id,
            "rfi_number": rfi.rfi_number,
            "rfi_title": rfi.rfi_title
        })
    
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
                tenant_id = 1  # Default tenant for development
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"[RFI] No tenant found in request, using default tenant_id=1 for development")
        
        # Get or create admin user for development (race-safe bootstrap)
        admin_user = _get_or_create_dev_superuser()
        
        # Get user_id from request.user if available
        user_id = None
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            if hasattr(request.user, 'userid'):
                user_id = request.user.userid
            elif hasattr(request.user, 'id'):
                user_id = request.user.id
            elif hasattr(request.user, 'UserId'):
                user_id = request.user.UserId
        
        # Use user_id if available, otherwise use admin_user
        created_by = user_id if user_id else admin_user.id
        
        data = request.data.copy() if hasattr(request.data, 'copy') else request.data
        
        # Add tenant_id to data if not present
        if 'tenant_id' not in data and 'tenant' not in data:
            data['tenant_id'] = tenant_id
        
        # Add created_by to data if not present (will be ignored if read_only, but helps with validation)
        if 'created_by' not in data:
            data['created_by'] = created_by
        
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
            # Save with created_by and tenant_id (these will override any values in validated_data)
            serializer.save(created_by=created_by, tenant_id=tenant_id)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            import traceback
            print(f"Exception during RFI creation: {str(e)}")
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Override update to handle tenant and user assignment - supports upsert (create if not exists)"""
        partial = kwargs.pop('partial', False)
        pk = kwargs.get('pk') or self.kwargs.get('pk')
        
        try:
            instance = self.get_object()
        except NotFound:
            # If RFI doesn't exist, create it instead (upsert behavior)
            # This handles the case where frontend has stale ID in localStorage
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"[RFI Update] RFI with ID {pk} not found. Creating new RFI instead (upsert).")
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
            
            # If still no tenant_id, use the instance's tenant_id or default to 1
            if not tenant_id:
                tenant_id = getattr(instance, 'tenant_id', None) or 1
        
        # Prepare data
        data = request.data.copy() if hasattr(request.data, 'copy') else request.data
        if 'tenant_id' not in data:
            data['tenant_id'] = tenant_id
        
        serializer = self.get_serializer(instance, data=data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data)
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[RFI Update] Error updating RFI: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RFIEvaluationCriteriaViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing RFI evaluation criteria
    """
    queryset = RFIEvaluationCriteria.objects.all()
    serializer_class = RFIEvaluationCriteriaSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Filter by RFI and tenant"""
        queryset = super().get_queryset()
        rfi_id = self.request.query_params.get('rfi_id', None)
        tenant_id = get_tenant_id_from_request(self.request)
        
        if rfi_id:
            queryset = queryset.filter(rfi_id=rfi_id)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Override list to handle DELETE requests with rfi_id for bulk delete"""
        # Handle DELETE requests with rfi_id query param (bulk delete)
        if request.method == 'DELETE':
            rfi_id = request.query_params.get('rfi_id', None)
            if rfi_id:
                tenant_id = get_tenant_id_from_request(request)
                if not tenant_id:
                    tenant_id = 1  # Default for development
                
                queryset = self.get_queryset().filter(rfi_id=rfi_id)
                if tenant_id:
                    queryset = queryset.filter(tenant_id=tenant_id)
                
                count = queryset.count()
                queryset.delete()
                return Response({'deleted_count': count}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {"error": "rfi_id query parameter is required for bulk delete"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Normal GET list behavior
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        """Bulk delete evaluation criteria by rfi_id"""
        rfi_id = request.query_params.get('rfi_id', None)
        if not rfi_id:
            return Response(
                {"error": "rfi_id query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            tenant_id = 1  # Default for development
        
        queryset = self.get_queryset().filter(rfi_id=rfi_id)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        count = queryset.count()
        queryset.delete()
        return Response({'deleted_count': count}, status=status.HTTP_204_NO_CONTENT)
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to handle bulk delete by rfi_id"""
        rfi_id = request.query_params.get('rfi_id', None)
        if rfi_id and not kwargs.get('pk'):
            # Bulk delete all criteria for this RFI
            tenant_id = get_tenant_id_from_request(request)
            if not tenant_id:
                tenant_id = 1  # Default for development
            
            queryset = self.get_queryset().filter(rfi_id=rfi_id)
            if tenant_id:
                queryset = queryset.filter(tenant_id=tenant_id)
            count = queryset.count()
            queryset.delete()
            return Response({'deleted_count': count}, status=status.HTTP_204_NO_CONTENT)
        return super().destroy(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """Override create to set tenant and created_by"""
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
                tenant_id = 1  # Default tenant for development
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"[RFI Evaluation Criteria] No tenant found in request, using default tenant_id=1 for development")
        
        # Get or create admin user for development (race-safe bootstrap)
        admin_user = _get_or_create_dev_superuser()
        
        # Get user_id from request.user if available
        user_id = None
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            if hasattr(request.user, 'userid'):
                user_id = request.user.userid
            elif hasattr(request.user, 'id'):
                user_id = request.user.id
            elif hasattr(request.user, 'UserId'):
                user_id = request.user.UserId
        
        # Use user_id if available, otherwise use admin_user
        created_by = user_id if user_id else admin_user.id
        
        data = request.data.copy()
        if 'tenant_id' not in data:
            data['tenant_id'] = tenant_id
        
        # Add created_by to data if not present (will be ignored if read_only, but helps with validation)
        if 'created_by' not in data:
            data['created_by'] = created_by
        
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
            # Save with created_by and tenant_id (these will override any values in validated_data)
            serializer.save(created_by=created_by, tenant_id=tenant_id)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            import traceback
            print(f"Exception during RFI Evaluation Criteria creation: {str(e)}")
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RFITypeView(APIView):
    """API endpoint for getting RFI types"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get list of unique RFI types from existing RFIs"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
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
                            except Exception as e:
                                logger.warning(f"[RFI Types] Error getting tenant from user: {str(e)}")
                    except Exception as e:
                        logger.warning(f"[RFI Types] Error processing user tenant: {str(e)}")
                
                # If still no tenant_id, use default tenant (1) for development
                if not tenant_id:
                    tenant_id = 1
                    logger.info(f"[RFI Types] Using default tenant_id=1 for development")
            
            logger.info(f"[RFI Types] Fetching RFI types for tenant_id={tenant_id}")
            
            queryset = RFI.objects.all()
            if tenant_id:
                queryset = queryset.filter(tenant_id=tenant_id)
            
            rfi_types = queryset.values_list('rfi_type', flat=True).distinct().order_by('rfi_type')
            rfi_types_list = list(rfi_types)
            
            logger.info(f"[RFI Types] Found {len(rfi_types_list)} unique RFI types")
            
            return Response({
                'success': True,
                'rfi_types': rfi_types_list
            })
        except Exception as e:
            import traceback
            logger.error(f"[RFI Types] Error fetching RFI types: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({
                'success': False,
                'error': str(e),
                'rfi_types': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
