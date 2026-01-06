"""
URL configuration for vendor_auth app
"""

from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_endpoint, name='test_endpoint'),
    path('login/', views.simple_login, name='simple_login'),
    path('logout/', views.logout, name='logout'),
    path('check-auth/', views.check_auth, name='check_auth'),
]