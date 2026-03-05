"""
Vendor Questionnaire URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    QuestionnaireViewSet,
    QuestionnaireQuestionViewSet,
    QuestionnaireAssignmentViewSet,
    QuestionnaireResponseViewSet,
    get_assignment_by_token_view,
    save_responses_by_token_view,
    submit_final_by_token_view,
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'questionnaires', QuestionnaireViewSet, basename='questionnaire')
router.register(r'questions', QuestionnaireQuestionViewSet, basename='questionnaire-question')
router.register(r'assignments', QuestionnaireAssignmentViewSet, basename='questionnaire-assignment')
router.register(r'responses', QuestionnaireResponseViewSet, basename='questionnaire-response')

urlpatterns = [
    path('', include(router.urls)),
    # Public questionnaire response (no authentication)
    path('public/assignment/', get_assignment_by_token_view),
    path('public/save_responses/', save_responses_by_token_view),
    path('public/submit_final/', submit_final_by_token_view),
]
