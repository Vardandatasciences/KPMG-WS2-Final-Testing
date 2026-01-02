from rest_framework import serializers
from .models import User, MfaEmailChallenge, MfaAuditLog


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['userid', 'username', 'email', 'first_name', 'last_name', 'is_active']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['is_active'] = instance.is_active  # Use the property
        return data


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=255, write_only=True)
    
    def validate_username(self, value):
        if not value.strip():
            raise serializers.ValidationError("Username cannot be empty")
        return value.strip()


class OtpVerificationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    otp = serializers.CharField(max_length=6, min_length=6)
    
    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits")
        return value


class LoginResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    requires_otp = serializers.BooleanField(default=False)
    user = UserSerializer(required=False)
    session_token = serializers.CharField(required=False)


class OtpResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    user = UserSerializer(required=False)
    session_token = serializers.CharField(required=False)


class MfaChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MfaEmailChallenge
        fields = ['challenge_id', 'status', 'attempts', 'expires_at', 'created_at']
        read_only_fields = ['challenge_id', 'expires_at', 'created_at']


class MfaAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MfaAuditLog
        fields = ['mfa_event_id', 'event_type', 'detail_json', 'ip_address', 'created_at']
        read_only_fields = ['mfa_event_id', 'created_at']
