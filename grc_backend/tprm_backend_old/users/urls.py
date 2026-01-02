"""
URL patterns for the users app.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User management
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('approvers/', views.ApproverListView.as_view(), name='approver-list'),
    
    # Sessions
    path('sessions/', views.UserSessionListView.as_view(), name='session-list'),
    path('sessions/<int:session_id>/terminate/', views.terminate_session, name='terminate-session'),
    
    # Preferences
    path('notifications/', views.NotificationPreferencesView.as_view(), name='notification-preferences'),
    
    # Current user
    path('me/', views.current_user, name='current-user'),
    path('stats/', views.user_stats, name='user-stats'),
]
