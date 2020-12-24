from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

from api.views import QuestionViewSet, SampleMultipleChoiceQuestionViewSet, UserConsentViewSet, ContactUsViewSet, \
    QuestionCategoryViewSet, UserStatsViewSet

router = DefaultRouter()
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'sample-multiple-choice-question', SampleMultipleChoiceQuestionViewSet,
                basename='sample_multiple_choice_question')
router.register(r'user-consent', UserConsentViewSet, basename='user_consent')
router.register(r'contact-us', ContactUsViewSet, basename='contact_us')
router.register(r'question-category', QuestionCategoryViewSet, basename='question-category')
router.register(r'user-stats', UserStatsViewSet, basename='user-stats')

app_name = 'api'
urlpatterns = [
    path('openapi', get_schema_view(
        title="Canvas Gamification API",
        description="All the available APIs",
        version="1.0.0",
    ), name='openapi-schema')
] + router.urls
