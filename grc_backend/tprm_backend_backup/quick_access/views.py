from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes as permission_classes_decorator
from rest_framework.response import Response
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission, AllowAny
from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import jwt
import logging
from .models import GRCLog, QuickAccessFavorite
from .serializers import (
    GRCLogSerializer, QuickAccessFavoriteSerializer, 
    DashboardStatsSerializer, ActivitySummarySerializer, SuggestionSerializer
)

# Use Unified JWT Authentication from GRC
from grc.jwt_auth import UnifiedJWTAuthentication

logger = logging.getLogger(__name__)


class SimpleAuthenticatedPermission(BasePermission):
    """Custom permission class that checks for authenticated users"""
    def has_permission(self, request, view):
        # Just check if user object exists and is authenticated
        # UnifiedJWTAuthentication handles GRC/TPRM user verification
        if request.user and hasattr(request.user, 'is_authenticated'):
            return request.user.is_authenticated
        return False


# REMOVED BUGGY LOCAL JWT CLASS - Using UnifiedJWTAuthentication from grc.jwt_auth instead


class GRCLogViewSet(viewsets.ModelViewSet):
    queryset = GRCLog.objects.all()
    serializer_class = GRCLogSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]  # Proper GRC user authentication
    pagination_class = None  # Disable pagination

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id', 2)
        days = self.request.query_params.get('days', 7)
        
        try:
            # Filter by user_id (default to 2) - convert to string to match database field type
            queryset = queryset.filter(user_id=str(user_id))
            
            # Filter by days
            if days:
                try:
                    days = int(days)
                    start_date = timezone.now() - timedelta(days=days)
                    queryset = queryset.filter(timestamp__gte=start_date)
                except ValueError:
                    pass
            
            return queryset.order_by('-timestamp')
        except Exception as e:
            print(f"Error in GRCLogViewSet.get_queryset: {e}")
            return queryset.none()

    @action(detail=False, methods=['get'])
    def recent_activities(self, request):
        """Get recent activities for a user"""
        try:
            user_id = request.query_params.get('user_id', 2)
            days = request.query_params.get('days', 7)
            
            try:
                days = int(days)
                start_date = timezone.now() - timedelta(days=days)
                
                # First try to get user-specific activities
                activities = GRCLog.objects.filter(
                    user_id=str(user_id),
                    timestamp__gte=start_date
                ).order_by('-timestamp')[:20]
                
                # If no user-specific activities, show system-wide activities
                if not activities.exists():
                    print(f"No activities for user {user_id} in last {days} days, showing system-wide activities")
                    activities = GRCLog.objects.filter(
                        timestamp__gte=start_date
                    ).order_by('-timestamp')[:20]
                
                serializer = self.get_serializer(activities, many=True)
                return Response(serializer.data)
            except Exception as db_error:
                print(f"Database error in recent_activities: {db_error}")
                return Response([])
        except Exception as e:
            print(f"Error in recent_activities: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def activity_summary(self, request):
        """Get activity summary by module"""
        try:
            user_id = request.query_params.get('user_id', 2)
            days = request.query_params.get('days', 30)
            
            try:
                days = int(days)
                start_date = timezone.now() - timedelta(days=days)
                
                # Get activity counts by module
                module_counts = GRCLog.objects.filter(
                    user_id=str(user_id),
                    timestamp__gte=start_date
                ).values('module').annotate(count=Count('log_id')).order_by('-count')
                
                summary = []
                for module_data in module_counts:
                    module = module_data['module']
                    count = module_data['count']
                    
                    # Get recent activities for this module
                    activities = GRCLog.objects.filter(
                        user_id=str(user_id),
                        module=module,
                        timestamp__gte=start_date
                    ).order_by('-timestamp')[:5]
                    
                    summary.append({
                        'module': module,
                        'count': count,
                        'activities': GRCLogSerializer(activities, many=True).data
                    })
                
                return Response(summary)
            except Exception as db_error:
                print(f"Database error in activity_summary: {db_error}")
                return Response([])
        except Exception as e:
            print(f"Error in activity_summary: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QuickAccessFavoriteViewSet(viewsets.ModelViewSet):
    queryset = QuickAccessFavorite.objects.all()
    serializer_class = QuickAccessFavoriteSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]  # Proper GRC user authentication
    pagination_class = None  # Disable pagination

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id', 2)
        try:
            # Convert user_id to integer to match database field type
            user_id = int(user_id)
            filtered_queryset = queryset.filter(user_id=user_id).order_by('order', 'created_at')
            print(f"QuickAccessFavoriteViewSet: user_id={user_id}, count={filtered_queryset.count()}")
            return filtered_queryset
        except Exception as e:
            print(f"Error in QuickAccessFavoriteViewSet.get_queryset: {e}")
            return queryset.none()

    def list(self, request, *args, **kwargs):
        """Override list method to add debugging"""
        print(f"QuickAccessFavoriteViewSet.list called with params: {request.query_params}")
        queryset = self.get_queryset()
        print(f"Queryset count: {queryset.count()}")
        serializer = self.get_serializer(queryset, many=True)
        print(f"Serialized data: {serializer.data}")
        return Response(serializer.data)

    def perform_create(self, serializer):
        from django.db import IntegrityError
        from rest_framework.exceptions import ValidationError
        try:
            user_id = self.request.data.get('user_id', 2)
            
            # Validate required fields
            title = self.request.data.get('title')
            url = self.request.data.get('url')
            module = self.request.data.get('module')
            entity_type = self.request.data.get('entity_type')
            entity_id = self.request.data.get('entity_id', '')
            
            # Log the incoming data for debugging
            print(f"Creating favorite with data: user_id={user_id}, title={title}, url={url}, module={module}, entity_type={entity_type}, entity_id={entity_id}")
            
            if not title:
                raise ValidationError({"title": "Title is required"})
            if not url:
                raise ValidationError({"url": "URL is required"})
            if not module:
                raise ValidationError({"module": "Module is required"})
            if not entity_type:
                raise ValidationError({"entity_type": "Entity type is required"})
            
            # Check for duplicate URL
            existing_url = QuickAccessFavorite.objects.filter(
                user_id=user_id,
                url=url
            ).first()
            
            if existing_url:
                print(f"Duplicate URL found: {url}")
                raise ValidationError({"detail": "A favorite with this URL already exists"})
            
            # Check for duplicate module + entity_id (only if entity_id is provided and not empty)
            if entity_id and entity_id.strip():
                existing = QuickAccessFavorite.objects.filter(
                    user_id=user_id,
                    module=module,
                    entity_id=entity_id
                ).first()
                
                if existing:
                    print(f"Duplicate module+entity_id found: {module}/{entity_id}")
                    raise ValidationError({"detail": "A favorite with this module and entity already exists"})
            
            print(f"Saving favorite for user {user_id}")
            serializer.save(user_id=user_id)
            print(f"Favorite saved successfully")
        except ValidationError as e:
            print(f"Validation error in perform_create: {e}")
            raise
        except IntegrityError as e:
            print(f"Integrity error in perform_create: {e}")
            raise ValidationError({"detail": f"Database constraint violation: {str(e)}"})
        except Exception as e:
            print(f"Unexpected error in perform_create: {e}")
            import traceback
            traceback.print_exc()
            raise ValidationError({"detail": f"An error occurred: {str(e)}"})


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes_decorator([AllowAny])  # Temporarily allow all for testing
def dashboard_stats(request):
    """Get dashboard statistics for quick access"""
    try:
        user_id = int(request.GET.get('user_id', 2))
        
        # Initialize default stats
        stats = {
            'today_activities': 0,
            'week_activities': 0,
            'favorites_count': 0,
            'most_active_module': 'N/A'
        }
        
        try:
            # Today's activities (system-wide for dashboard view)
            today = timezone.now().date()
            today_activities = GRCLog.objects.filter(
                timestamp__date=today
            ).count()
            stats['today_activities'] = today_activities
            
            # This week's activities (system-wide for dashboard view)
            week_start = today - timedelta(days=today.weekday())
            week_activities = GRCLog.objects.filter(
                timestamp__date__gte=week_start
            ).count()
            stats['week_activities'] = week_activities
            
            # Favorites count (user-specific)
            favorites_count = QuickAccessFavorite.objects.filter(user_id=user_id).count()
            print(f"Dashboard stats: user_id={user_id}, today={today_activities}, week={week_activities}, favorites={favorites_count}")
            stats['favorites_count'] = favorites_count
            
            # Most active module (user-specific, last 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            most_active = GRCLog.objects.filter(
                user_id=str(user_id),
                timestamp__gte=thirty_days_ago
            ).values('module').annotate(count=Count('log_id')).order_by('-count').first()
            
            if most_active:
                stats['most_active_module'] = most_active['module']
            else:
                # If no user-specific activity, get system-wide most active module
                most_active_system = GRCLog.objects.filter(
                    timestamp__gte=thirty_days_ago
                ).values('module').annotate(count=Count('log_id')).order_by('-count').first()
                if most_active_system:
                    stats['most_active_module'] = most_active_system['module']
                
        except Exception as db_error:
            # If database operations fail, return default stats
            print(f"Database error in dashboard_stats: {db_error}")
            import traceback
            traceback.print_exc()
            pass
        
        return Response(stats)
    except Exception as e:
        print(f"Error in dashboard_stats: {e}")
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes_decorator([AllowAny])  # Temporarily allow all for testing
def get_suggestions(request):
    """Get smart suggestions based on user activity"""
    try:
        user_id = int(request.GET.get('user_id', 2))
        suggestions = []
        
        try:
            # Get user's recent activities to generate suggestions
            recent_activities = GRCLog.objects.filter(
                user_id=str(user_id)
            ).order_by('-timestamp')[:50]
            
            # Analyze patterns and generate suggestions
            modules_used = set()
            action_types = set()
            
            for activity in recent_activities:
                modules_used.add(activity.module)
                action_types.add(activity.action_type)
            
            # Generate suggestions based on patterns
            if 'SLA' in modules_used and 'VIEW' in action_types:
                suggestions.append({
                    'title': 'SLA Performance Dashboard',
                    'url': '/performance',
                    'module': 'SLA',
                    'reason': 'You frequently view SLAs. Check the performance dashboard.',
                    'confidence': 0.8,
                    'icon': 'fas fa-chart-line',
                    'entity_type': 'Performance',
                    'entity_id': 'SLA_PERF_SUGGEST'
                })
            
            if 'Contract' in modules_used:
                suggestions.append({
                    'title': 'Contract Analytics',
                    'url': '/analytics',
                    'module': 'Contract',
                    'reason': 'Based on your contract activity, review analytics and insights.',
                    'confidence': 0.7,
                    'icon': 'fas fa-chart-bar',
                    'entity_type': 'Analytics',
                    'entity_id': 'CONTRACT_ANALYTICS_SUGGEST'
                })
            
            if 'Vendor' not in modules_used:
                suggestions.append({
                    'title': 'Explore Vendor Management',
                    'url': '/vendor-dashboard',
                    'module': 'Vendor',
                    'reason': 'You haven\'t used vendor management yet. It might be useful for your workflow.',
                    'confidence': 0.6,
                    'icon': 'fas fa-building',
                    'entity_type': 'Vendor',
                    'entity_id': 'VENDOR_SUGGEST'
                })
            
            if 'RFP' not in modules_used:
                suggestions.append({
                    'title': 'Explore RFP Management',
                    'url': '/rfp-dashboard',
                    'module': 'RFP',
                    'reason': 'Start managing RFPs efficiently with our workflow tools.',
                    'confidence': 0.6,
                    'icon': 'fas fa-file-invoice',
                    'entity_type': 'RFP',
                    'entity_id': 'RFP_SUGGEST'
                })
                
        except Exception as db_error:
            print(f"Database error in get_suggestions: {db_error}")
            pass
        
        # Add some default suggestions if none generated
        if not suggestions:
            suggestions = [
                {
                    'title': 'SLA Dashboard',
                    'url': '/dashboard',
                    'module': 'SLA',
                    'reason': 'Monitor your SLA performance and metrics.',
                    'confidence': 0.5,
                    'icon': 'fas fa-tachometer-alt',
                    'entity_type': 'Dashboard',
                    'entity_id': 'SLA_DASH_DEFAULT'
                },
                {
                    'title': 'Contract Management',
                    'url': '/contractdashboard',
                    'module': 'Contract',
                    'reason': 'Manage and track all your contracts in one place.',
                    'confidence': 0.5,
                    'icon': 'fas fa-file-contract',
                    'entity_type': 'Dashboard',
                    'entity_id': 'CONTRACT_DEFAULT'
                },
                {
                    'title': 'Vendor Dashboard',
                    'url': '/vendor-dashboard',
                    'module': 'Vendor',
                    'reason': 'Track vendor relationships and performance.',
                    'confidence': 0.5,
                    'icon': 'fas fa-building',
                    'entity_type': 'Dashboard',
                    'entity_id': 'VENDOR_DEFAULT'
                }
            ]
        
        return Response(suggestions)
    except Exception as e:
        print(f"Error in get_suggestions: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes_decorator([AllowAny])  # Temporarily allow all for testing
def test_connection(request):
    """Test database connection and return basic info"""
    try:
        # Test GRCLog model
        grc_count = GRCLog.objects.count()
        
        # Test QuickAccessFavorite model
        favorites_count = QuickAccessFavorite.objects.count()
        
        return Response({
            'status': 'success',
            'grc_logs_count': grc_count,
            'favorites_count': favorites_count,
            'message': 'Database connection successful'
        })
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
