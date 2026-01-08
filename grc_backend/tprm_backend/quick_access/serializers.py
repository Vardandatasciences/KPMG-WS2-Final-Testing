from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import GRCLog, QuickAccessFavorite


class GRCLogSerializer(AutoDecryptingModelSerializer):
    time_since = serializers.SerializerMethodField()
    
    class Meta:
        model = GRCLog
        fields = [
            'log_id', 'timestamp', 'user_id', 'user_name', 'module',
            'action_type', 'entity_id', 'entity_type', 'log_level',
            'description', 'ip_address', 'additional_info', 'time_since'
        ]

    def get_time_since(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.timestamp
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"


class QuickAccessFavoriteSerializer(AutoDecryptingModelSerializer):
    class Meta:
        model = QuickAccessFavorite
        fields = [
            'id', 'user_id', 'title', 'url', 'module', 'entity_type',
            'entity_id', 'icon', 'created_at', 'order'
        ]


class DashboardStatsSerializer(serializers.Serializer):
    today_activities = serializers.IntegerField()
    week_activities = serializers.IntegerField()
    favorites_count = serializers.IntegerField()
    most_active_module = serializers.CharField()


class ActivitySummarySerializer(serializers.Serializer):
    module = serializers.CharField()
    count = serializers.IntegerField()
    activities = GRCLogSerializer(many=True)


class SuggestionSerializer(serializers.Serializer):
    title = serializers.CharField()
    url = serializers.CharField()
    module = serializers.CharField()
    reason = serializers.CharField()
    confidence = serializers.FloatField()
    icon = serializers.CharField()
    entity_type = serializers.CharField()
    entity_id = serializers.CharField()
