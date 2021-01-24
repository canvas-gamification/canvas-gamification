from django.urls import path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view
from rest_framework.authtoken import views

from api.views import QuestionViewSet, SampleMultipleChoiceQuestionViewSet, UserConsentViewSet, ContactUsViewSet, \
    QuestionCategoryViewSet, UserStatsViewSet, UserRegistrationViewSet, UserProfileDetailsViewSet

router = DefaultRouter()
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'sample-multiple-choice-question', SampleMultipleChoiceQuestionViewSet,
                basename='sample_multiple_choice_question')
router.register(r'user-consent', UserConsentViewSet, basename='user_consent')
router.register(r'contact-us', ContactUsViewSet, basename='contact_us')
router.register(r'question-category', QuestionCategoryViewSet, basename='question-category')
router.register(r'user-stats', UserStatsViewSet, basename='user-stats')
router.register(r'user-consent', UserConsentViewSet, basename='user-consent')
router.register(r'register', UserRegistrationViewSet, basename='register')
router.register(r'update-profile', UserProfileDetailsViewSet, basename='update-profile')

app_name = 'api'
urlpatterns = [
    path('openapi', get_schema_view(
        title="Canvas Gamification API",
        description="All the available APIs",
        version="1.0.0",
    ), name='openapi-schema'),
    path('docs/', TemplateView.as_view(
        template_name='api/docs.html',
        extra_context={'schema_url': 'api:openapi-schema'}
    ), name='docs'),
    path('api-token-auth/', views.obtain_auth_token)
] + router.urls
