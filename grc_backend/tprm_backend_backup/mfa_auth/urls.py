from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_step1, name='login_step1'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('validate-session/', views.validate_session, name='validate_session'),
    path('refresh-token/', views.refresh_token, name='refresh_token'),
    path('logout/', views.logout, name='logout'),
    path('status/', views.mfa_status, name='mfa_status'),
    path('active-sessions/', views.active_sessions, name='active_sessions'),
    path('force-logout/', views.force_logout, name='force_logout'),
]
