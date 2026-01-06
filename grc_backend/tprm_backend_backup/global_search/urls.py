from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GlobalSearchViewSet, SearchAnalyticsViewSet

router = DefaultRouter()
router.register(r'analytics', SearchAnalyticsViewSet, basename='search-analytics')

urlpatterns = [
    path('', include(router.urls)),
    
    # Global Search endpoints
    path('query/', GlobalSearchViewSet.as_view({'post': 'search_query'}), name='search-query'),
    path('stats/', GlobalSearchViewSet.as_view({'get': 'search_stats'}), name='search-stats'),
    
    # Dashboard Analytics endpoints
    path('dashboard-analytics/', GlobalSearchViewSet.as_view({'get': 'dashboard_analytics'}), name='dashboard-analytics'),
    path('live-updates/', GlobalSearchViewSet.as_view({'get': 'live_updates'}), name='live-updates'),
    
    # Filter options endpoint
    path('filter-options/', GlobalSearchViewSet.as_view({'get': 'get_filter_options'}), name='filter-options'),
    
    # Search History endpoints
    path('history/', GlobalSearchViewSet.as_view({'get': 'search_history', 'delete': 'clear_search_history'}), name='search-history'),
    
    # Index management endpoints
    path('index/update/', GlobalSearchViewSet.as_view({'post': 'update_index'}), name='update-index'),
    path('index/bulk-update/', GlobalSearchViewSet.as_view({'post': 'bulk_update_index'}), name='bulk-update-index'),
    path('index/delete/', GlobalSearchViewSet.as_view({'delete': 'delete_index_entry'}), name='delete-index-entry'),
]
