"""
Serializers for Admin Access Control
"""
from rest_framework import serializers
from django.db import models
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import User, RBACTPRM


class UserSerializer(AutoDecryptingModelSerializer):
    """Serializer for User model"""
    full_name = serializers.SerializerMethodField()
    total_permissions = serializers.SerializerMethodField()
    permission_display = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['userid', 'username', 'email', 'firstname', 'lastname', 
                  'full_name', 'isactive', 'departmentid', 'total_permissions', 
                  'permission_display', 'createdat', 'updatedat']
    
    def get_full_name(self, obj):
        if obj.firstname and obj.lastname:
            return f"{obj.firstname} {obj.lastname}"
        return obj.username
    
    def get_total_permissions(self, obj):
        """Count total active permissions for user"""
        try:
            rbac = RBACTPRM.objects.filter(user_id=obj.userid, is_active='Y').first()
            if rbac:
                # Count all boolean fields that are True
                permission_fields = [f.name for f in RBACTPRM._meta.fields 
                                   if isinstance(f, models.BooleanField)]
                count = sum(1 for field in permission_fields if getattr(rbac, field, False))
                return count
        except Exception as e:
            print(f"Error counting permissions for user {obj.userid}: {e}")
        return 0
    
    def get_permission_display(self, obj):
        """Get permission display in format 'X / Total'"""
        try:
            # Get total number of available permission fields
            total_available = len([f.name for f in RBACTPRM._meta.fields 
                                  if isinstance(f, models.BooleanField)])
            
            # Get user's active permissions count
            user_permissions = self.get_total_permissions(obj)
            
            return f"{user_permissions} / {total_available}"
        except Exception as e:
            print(f"Error getting permission display for user {obj.userid}: {e}")
            return "0 / 0"


class RBACTPRMSerializer(AutoDecryptingModelSerializer):
    """Serializer for RBAC TPRM permissions"""
    
    class Meta:
        model = RBACTPRM
        fields = '__all__'
    
    def to_representation(self, instance):
        """
        Convert database representation to API response format
        Using the same categorization logic as tprm_utils.py for consistency
        """
        data = super().to_representation(instance)
        
        # Organize permissions by module (matching tprm_utils.py categorization)
        permissions = {
            'userId': data.get('user_id'),
            'userName': data.get('username'),
            'role': data.get('role'),
            'permissions': {
                'rfp': {},
                'contract': {},
                'vendor': {},
                'risk': {},
                'compliance': {},
                'bcp_drp': {},
                'sla': {},
                'questionnaire': {},
                'system': {}
            }
        }
        
        # Map all permission fields to their respective modules
        # Using the same logic as tprm_utils.py get_user_permissions_summary()
        for key, value in data.items():
            if key in ['rbac_id', 'user_id', 'username', 'role', 'created_at', 'updated_at', 'is_active']:
                continue
                
            # Categorize by module (same logic as tprm_utils.py)
            key_lower = key.lower()
            if 'rfp' in key_lower:
                permissions['permissions']['rfp'][key] = value
            elif 'contract' in key_lower:
                permissions['permissions']['contract'][key] = value
            elif 'vendor' in key_lower:
                permissions['permissions']['vendor'][key] = value
            elif 'risk' in key_lower:
                permissions['permissions']['risk'][key] = value
            elif 'compliance' in key_lower or 'audit' in key_lower:
                permissions['permissions']['compliance'][key] = value
            elif 'bcp' in key_lower or 'drp' in key_lower:
                permissions['permissions']['bcp_drp'][key] = value
            elif 'sla' in key_lower or 'performance' in key_lower or 'alert' in key_lower:
                permissions['permissions']['sla'][key] = value
            elif 'questionnaire' in key_lower:
                permissions['permissions']['questionnaire'][key] = value
            else:
                permissions['permissions']['system'][key] = value
        
        return permissions


class PermissionUpdateSerializer(serializers.Serializer):
    """Serializer for updating user permissions"""
    user_id = serializers.IntegerField(required=True)
    permissions = serializers.DictField(child=serializers.BooleanField(), required=True)
    role = serializers.CharField(required=False, allow_blank=True, max_length=100)
    
    def validate_user_id(self, value):
        """Validate that the user exists"""
        if not User.objects.filter(userid=value, isactive='Y').exists():
            raise serializers.ValidationError("User not found or inactive")
        return value


class PermissionFieldSerializer(serializers.Serializer):
    """Serializer for permission field metadata"""
    field_name = serializers.CharField()
    db_column = serializers.CharField()
    module = serializers.CharField()
    display_name = serializers.CharField()
    description = serializers.CharField()

