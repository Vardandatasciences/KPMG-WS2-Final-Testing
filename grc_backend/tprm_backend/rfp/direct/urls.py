from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'direct-procurements', views.DirectProcurementViewSet)
router.register(r'direct-evaluation-criteria', views.DirectEvaluationCriteriaViewSet)

urlpatterns = [
    path('direct-types/types/', views.DirectTypeView.as_view(), name='direct-types'),
    path('', include(router.urls)),
]
