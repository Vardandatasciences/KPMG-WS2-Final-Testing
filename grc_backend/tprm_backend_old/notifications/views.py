from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes as permission_classes_decorator
from rest_framework.response import Response
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission, AllowAny
from django.db.models import Count, Q
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import jwt
import logging
from .models import Notification
from .serializers import NotificationSerializer, NotificationStatsSerializer

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


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [SimpleAuthenticatedPermission]  # Proper GRC user authentication
    
    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            
            # Filter by unread only
            unread_only = self.request.query_params.get('unread_only', 'false').lower() == 'true'
            if unread_only:
                queryset = queryset.exclude(status='read')
            
            # Filter by priority
            priority = self.request.query_params.getlist('priority')
            if priority:
                queryset = queryset.filter(priority__in=priority)
            
            # Filter by type
            notification_type = self.request.query_params.getlist('type')
            if notification_type:
                queryset = queryset.filter(notification_type__in=notification_type)
            
            # Filter by status
            status_filter = self.request.query_params.getlist('status')
            if status_filter:
                queryset = queryset.filter(status__in=status_filter)
            
            # Filter by date range
            date_from = self.request.query_params.get('date_from')
            date_to = self.request.query_params.get('date_to')
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)
            
            return queryset
        except Exception as e:
            # Handle database connection errors gracefully
            error_str = str(e).lower()
            if 'unknown server host' in error_str or '11001' in error_str or '2005' in error_str:
                logger.warning(f"Database connection error in get_queryset: {e}. Returning empty queryset.")
                # Return empty queryset when database is unreachable
                return Notification.objects.none()
            else:
                # Re-raise other errors
                logger.error(f"Error in get_queryset: {e}")
                raise
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.status = 'read'
        notification.read_at = timezone.now()
        notification.save()
        return Response({'status': 'marked as read'})
    
    @action(detail=True, methods=['delete'])
    def dismiss(self, request, pk=None):
        notification = self.get_object()
        notification.delete()
        return Response({'status': 'dismissed'})
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        try:
            # Get stats for the last 30 days
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            # Total counts
            total_sent = Notification.objects.count()
            total_read = Notification.objects.filter(status='read').count()
            total_unread = total_sent - total_read
            
            # Priority breakdown
            by_priority = {}
            for priority in ['critical', 'high', 'medium', 'low']:
                count = Notification.objects.filter(priority=priority).count()
                by_priority[priority] = count
            
            # Trends (comparing last 30 days to previous 30 days)
            last_30_days = Notification.objects.filter(created_at__gte=thirty_days_ago)
            previous_30_days = Notification.objects.filter(
                created_at__gte=thirty_days_ago - timedelta(days=30),
                created_at__lt=thirty_days_ago
            )
            
            sent_change = 0
            if previous_30_days.count() > 0:
                sent_change = ((last_30_days.count() - previous_30_days.count()) / previous_30_days.count()) * 100
            
            read_rate_change = 0
            if total_sent > 0:
                current_read_rate = (total_read / total_sent) * 100
                if previous_30_days.count() > 0:
                    prev_read_rate = (previous_30_days.filter(status='read').count() / previous_30_days.count()) * 100
                    read_rate_change = current_read_rate - prev_read_rate
            
            critical_alerts_change = 0
            current_critical = last_30_days.filter(priority='critical').count()
            if previous_30_days.count() > 0:
                prev_critical = previous_30_days.filter(priority='critical').count()
                if prev_critical > 0:
                    critical_alerts_change = ((current_critical - prev_critical) / prev_critical) * 100
            
            stats_data = {
                'total_sent': total_sent,
                'total_read': total_read,
                'total_unread': total_unread,
                'by_priority': by_priority,
                'trends': {
                    'sent_change': round(sent_change, 1),
                    'read_rate_change': round(read_rate_change, 1),
                    'critical_alerts_change': round(critical_alerts_change, 1)
                }
            }
            
            serializer = NotificationStatsSerializer(stats_data)
            return Response(serializer.data)
        except Exception as e:
            # Handle database connection errors gracefully
            error_str = str(e).lower()
            if 'unknown server host' in error_str or '11001' in error_str or '2005' in error_str:
                logger.warning(f"Database connection error in notification stats: {e}. Returning empty stats.")
                # Return empty stats when database is unreachable
                stats_data = {
                    'total_sent': 0,
                    'total_read': 0,
                    'total_unread': 0,
                    'by_priority': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                    'trends': {
                        'sent_change': 0,
                        'read_rate_change': 0,
                        'critical_alerts_change': 0
                    }
                }
                serializer = NotificationStatsSerializer(stats_data)
                return Response(serializer.data)
            else:
                # Re-raise other errors
                logger.error(f"Error in notification stats: {e}")
                raise

@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@permission_classes_decorator([AllowAny])  # Allow access for stats endpoint
def notification_stats(request):
    """
    Get notification statistics
    Note: Uses AllowAny permission to allow access even if JWT doesn't have user_id
    """
    """Function-based view for notification statistics"""
    try:
        # Get stats for the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Total counts
        total_sent = Notification.objects.count()
        total_read = Notification.objects.filter(status='read').count()
        total_unread = total_sent - total_read
        
        # Priority breakdown
        by_priority = {}
        for priority in ['critical', 'high', 'medium', 'low']:
            count = Notification.objects.filter(priority=priority).count()
            by_priority[priority] = count
        
        # Trends (comparing last 30 days to previous 30 days)
        last_30_days = Notification.objects.filter(created_at__gte=thirty_days_ago)
        previous_30_days = Notification.objects.filter(
            created_at__gte=thirty_days_ago - timedelta(days=30),
            created_at__lt=thirty_days_ago
        )
        
        sent_change = 0
        if previous_30_days.count() > 0:
            sent_change = ((last_30_days.count() - previous_30_days.count()) / previous_30_days.count()) * 100
        
        read_rate_change = 0
        if total_sent > 0:
            current_read_rate = (total_read / total_sent) * 100
            if previous_30_days.count() > 0:
                prev_read_rate = (previous_30_days.filter(status='read').count() / previous_30_days.count()) * 100
                read_rate_change = current_read_rate - prev_read_rate
        
        critical_alerts_change = 0
        current_critical = last_30_days.filter(priority='critical').count()
        if previous_30_days.count() > 0:
            prev_critical = previous_30_days.filter(priority='critical').count()
            if prev_critical > 0:
                critical_alerts_change = ((current_critical - prev_critical) / prev_critical) * 100
        
        stats_data = {
            'total_sent': total_sent,
            'total_read': total_read,
            'total_unread': total_unread,
            'by_priority': by_priority,
            'trends': {
                'sent_change': round(sent_change, 1),
                'read_rate_change': round(read_rate_change, 1),
                'critical_alerts_change': round(critical_alerts_change, 1)
            }
        }
        
        serializer = NotificationStatsSerializer(stats_data)
        return Response(serializer.data)
    except Exception as e:
        # Handle database connection errors gracefully
        error_str = str(e).lower()
        if 'unknown server host' in error_str or '11001' in error_str or '2005' in error_str:
            logger.warning(f"Database connection error in notification stats: {e}. Returning empty stats.")
            # Return empty stats when database is unreachable
            stats_data = {
                'total_sent': 0,
                'total_read': 0,
                'total_unread': 0,
                'by_priority': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                'trends': {
                    'sent_change': 0,
                    'read_rate_change': 0,
                    'critical_alerts_change': 0
                }
            }
            serializer = NotificationStatsSerializer(stats_data)
            return Response(serializer.data)
        else:
            # Re-raise other errors
            logger.error(f"Error in notification stats: {e}")
            raise