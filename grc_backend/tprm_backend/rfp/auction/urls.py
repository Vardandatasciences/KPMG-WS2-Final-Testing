from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'auctions', views.AuctionViewSet)
router.register(r'auction-evaluation-criteria', views.AuctionEvaluationCriteriaViewSet)

urlpatterns = [
    path('auction-types/types/', views.AuctionTypeView.as_view(), name='auction-types'),
    path('', include(router.urls)),
]
