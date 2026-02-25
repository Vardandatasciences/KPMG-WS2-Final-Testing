from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'emergency-procurements', views.EmergencyProcurementViewSet)
router.register(r'emergency-evaluation-criteria', views.EmergencyEvaluationCriteriaViewSet)

urlpatterns = [
    path('emergency-types/types/', views.EmergencyTypeView.as_view(), name='emergency-types'),
    path('', include(router.urls)),
]
