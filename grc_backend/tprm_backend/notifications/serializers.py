from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import Notification

class NotificationSerializer(AutoDecryptingModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'priority', 
            'channel', 'status', 'sender_id', 'recipient_id', 'created_at',
            'sent_at', 'delivered_at', 'read_at', 'metadata', 'external_id',
            'failed_reason', 'retry_count', 'max_retries'
        ]
        read_only_fields = ['id', 'created_at']

class NotificationStatsSerializer(serializers.Serializer):
    total_sent = serializers.IntegerField()
    total_read = serializers.IntegerField()
    total_unread = serializers.IntegerField()
    by_priority = serializers.DictField()
    trends = serializers.DictField()
