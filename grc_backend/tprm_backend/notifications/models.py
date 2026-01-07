from django.db import models
from django.contrib.auth.models import User
from tprm_backend.utils.encrypted_fields_mixin import TPRMEncryptedFieldsMixin

class Notification(TPRMEncryptedFieldsMixin, models.Model):
    PRIORITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    CHANNEL_CHOICES = [
        ('in_app', 'In App'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    sender_id = models.BigIntegerField()
    recipient_id = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    external_id = models.CharField(max_length=255, null=True, blank=True)
    failed_reason = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.priority}"