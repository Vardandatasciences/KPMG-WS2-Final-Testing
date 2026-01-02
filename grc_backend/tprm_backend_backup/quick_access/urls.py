from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GRCLogViewSet, QuickAccessFavoriteViewSet, dashboard_stats, get_suggestions, test_connection

router = DefaultRouter()
router.register(r'logs', GRCLogViewSet)
router.register(r'favorites', QuickAccessFavoriteViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard-stats/', dashboard_stats, name='dashboard-stats'),
    path('suggestions/', get_suggestions, name='suggestions'),
    path('test-connection/', test_connection, name='test-connection'),
]
