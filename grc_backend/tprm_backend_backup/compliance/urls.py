"""
URL configuration for compliance app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'frameworks', views.FrameworkViewSet)
router.register(r'compliance-mappings', views.ComplianceMappingViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
