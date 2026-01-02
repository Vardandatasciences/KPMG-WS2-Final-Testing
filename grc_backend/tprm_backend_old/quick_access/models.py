from django.db import models
import json


class GRCLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user_id = models.CharField(max_length=50)
    user_name = models.CharField(max_length=100)
    module = models.CharField(max_length=100)
    action_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=50, blank=True, null=True)
    entity_type = models.CharField(max_length=50, blank=True, null=True)
    log_level = models.CharField(max_length=20)
    description = models.TextField()
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    additional_info = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'grc_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user_name} - {self.action_type} - {self.module}"


class QuickAccessFavorite(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(default=1)
    title = models.CharField(max_length=200)
    url = models.CharField(max_length=500)
    module = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=50, blank=True, null=True)
    icon = models.CharField(max_length=50, default='fas fa-star')
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'quick_access_favorites'
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.title} - {self.module}"
