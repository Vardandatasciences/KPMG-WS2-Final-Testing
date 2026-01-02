from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, notification_stats

router = DefaultRouter()
router.register(r'', NotificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', notification_stats, name='notification-stats'),
]
