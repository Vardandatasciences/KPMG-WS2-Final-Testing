"""
Serializers for the users app.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import User, UserProfile, UserSession


class UserSerializer(AutoDecryptingModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'phone', 'department', 'position',
            'is_reviewer', 'review_level', 'sla_types',
            'auto_escalation', 'escalation_hours', 'escalation_to',
            'is_active', 'date_joined', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at', 'updated_at']


class UserProfileSerializer(AutoDecryptingModelSerializer):
    """Serializer for UserProfile model."""
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'avatar', 'bio', 'timezone',
            'notification_preferences', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSessionSerializer(AutoDecryptingModelSerializer):
    """Serializer for UserSession model."""
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'user', 'session_key', 'ip_address', 'user_agent',
            'created_at', 'last_activity', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'last_activity']


class RegisterSerializer(AutoDecryptingModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'user_type', 'phone',
            'department', 'position'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect')
        return value


class UserDetailSerializer(AutoDecryptingModelSerializer):
    """Detailed user serializer with profile information."""
    profile = UserProfileSerializer(read_only=True)
    escalation_to = UserSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'phone', 'department', 'position',
            'is_reviewer', 'review_level', 'sla_types',
            'auto_escalation', 'escalation_hours', 'escalation_to',
            'is_active', 'date_joined', 'created_at', 'updated_at',
            'profile'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at', 'updated_at']


class ApproverSerializer(AutoDecryptingModelSerializer):
    """Serializer for approver users."""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name',
            'review_level', 'sla_types', 'department',
            'auto_escalation', 'escalation_hours'
        ]
        read_only_fields = ['id']


class NotificationPreferencesSerializer(serializers.Serializer):
    """Serializer for notification preferences."""
    email_notifications = serializers.BooleanField(default=True)
    sms_notifications = serializers.BooleanField(default=False)
    slack_notifications = serializers.BooleanField(default=True)
    review_reminders = serializers.BooleanField(default=True)
    issue_notifications = serializers.BooleanField(default=True)
    report_notifications = serializers.BooleanField(default=False)
