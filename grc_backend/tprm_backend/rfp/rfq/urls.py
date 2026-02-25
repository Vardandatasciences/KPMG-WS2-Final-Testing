from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'rfqs', views.RFQViewSet)
router.register(r'rfq-evaluation-criteria', views.RFQEvaluationCriteriaViewSet)

urlpatterns = [
    path('rfq-types/types/', views.RFQTypeView.as_view(), name='rfq-types'),
    path('', include(router.urls)),
]
