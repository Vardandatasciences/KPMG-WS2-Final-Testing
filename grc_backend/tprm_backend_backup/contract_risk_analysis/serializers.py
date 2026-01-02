from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Risk


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


# Removed TPRMModuleSerializer and ModuleDataSerializer - using entity-data-row approach


class RiskSerializer(serializers.ModelSerializer):
    """Serializer for Risk model"""
    assigned_to_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Risk
        fields = '__all__'
        read_only_fields = ['id', 'score', 'priority', 'created_at', 'updated_at']
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(id=obj.assigned_to)
                return user.username
            except User.DoesNotExist:
                return f"User {obj.assigned_to}"
        return None
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(id=obj.created_by)
                return user.username
            except User.DoesNotExist:
                return f"User {obj.created_by}"
        return None


class RiskListSerializer(serializers.ModelSerializer):
    """Simplified serializer for risk list views"""
    assigned_to_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Risk
        fields = [
            'id', 'title', 'likelihood', 'impact', 'exposure_rating',
            'score', 'priority', 'status', 'risk_type', 'assigned_to_name', 'created_at',
            'description', 'ai_explanation', 'suggested_mitigations',
            'entity', 'data', 'row'
        ]
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(id=obj.assigned_to)
                return user.username
            except User.DoesNotExist:
                return f"User {obj.assigned_to}"
        return None


class RiskDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for risk detail views"""
    assigned_to = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    
    class Meta:
        model = Risk
        fields = '__all__'
    
    def get_assigned_to(self, obj):
        if obj.assigned_to:
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(id=obj.assigned_to)
                return UserSerializer(user).data
            except User.DoesNotExist:
                return None
        return None
    
    def get_created_by(self, obj):
        if obj.created_by:
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(id=obj.created_by)
                return UserSerializer(user).data
            except User.DoesNotExist:
                return None
        return None


class HeatmapDataSerializer(serializers.Serializer):
    """Serializer for dynamic heatmap data"""
    module_name = serializers.CharField()
    module_display_name = serializers.CharField()
    likelihood_range = serializers.CharField()
    impact_range = serializers.CharField()
    risk_count = serializers.IntegerField()
    average_score = serializers.FloatField()


# Removed RiskPredictionRequestSerializer - using entity-data-row approach


class RiskFilterSerializer(serializers.Serializer):
    """Serializer for risk filtering"""
    # Removed module field - using entity-data-row approach
    priority = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    risk_type = serializers.CharField(required=False, allow_blank=True)
    min_score = serializers.IntegerField(required=False, min_value=0, max_value=100)
    max_score = serializers.IntegerField(required=False, min_value=0, max_value=100)
    min_likelihood = serializers.IntegerField(required=False, min_value=1, max_value=5)
    max_likelihood = serializers.IntegerField(required=False, min_value=1, max_value=5)
    min_impact = serializers.IntegerField(required=False, min_value=1, max_value=5)
    max_impact = serializers.IntegerField(required=False, min_value=1, max_value=5)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    search = serializers.CharField(required=False, allow_blank=True)
    assigned_to = serializers.IntegerField(required=False)
