"""
Views for the users app.
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import User, UserProfile, UserSession
from .serializers import (
    UserSerializer, UserProfileSerializer, UserSessionSerializer,
    RegisterSerializer, LoginSerializer, ChangePasswordSerializer,
    UserDetailSerializer, ApproverSerializer, NotificationPreferencesSerializer
)


class RegisterView(APIView):
    """User registration view."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """User login view."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            refresh = RefreshToken.for_user(user)
            
            # Track session
            UserSession.objects.create(
                user=user,
                session_key=request.session.session_key,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """User logout view."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        logout(request)
        return Response({'message': 'Successfully logged out'})


class UserListView(generics.ListCreateAPIView):
    """List and create users."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user_type', 'department', 'is_approver', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['username', 'first_name', 'last_name', 'date_joined']
    ordering = ['username']


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete user."""
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserSerializer
        return UserDetailSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile view."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return get_object_or_404(UserProfile, user=self.request.user)


class ChangePasswordView(APIView):
    """Change password view."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApproverListView(generics.ListAPIView):
    """List approver users."""
    serializer_class = ApproverSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['review_level', 'department', 'sla_types']
    search_fields = ['username', 'first_name', 'last_name']
    
    def get_queryset(self):
        return User.objects.filter(is_reviewer=True, is_active=True)


class NotificationPreferencesView(APIView):
    """Notification preferences view."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        preferences = profile.notification_preferences
        serializer = NotificationPreferencesSerializer(data=preferences)
        serializer.is_valid()
        return Response(serializer.data)
    
    def put(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = NotificationPreferencesSerializer(data=request.data)
        if serializer.is_valid():
            profile.notification_preferences = serializer.validated_data
            profile.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSessionListView(generics.ListAPIView):
    """List user sessions."""
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_active']
    ordering_fields = ['created_at', 'last_activity']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def terminate_session(request, session_id):
    """Terminate a specific user session."""
    session = get_object_or_404(UserSession, id=session_id, user=request.user)
    session.is_active = False
    session.save()
    return Response({'message': 'Session terminated successfully'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    """Get current user information."""
    serializer = UserDetailSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """Get user statistics."""
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    approvers = User.objects.filter(is_approver=True).count()
    vendor_users = User.objects.filter(user_type='vendor').count()
    
    return Response({
        'total_users': total_users,
        'active_users': active_users,
        'approvers': approvers,
        'vendor_users': vendor_users,
    })
