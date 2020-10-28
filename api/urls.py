from rest_framework.routers import DefaultRouter

from api.views import QuestionViewSet, SampleMultipleChoiceQuestionViewSet, UserConsentViewSet, ContactUsViewSet

router = DefaultRouter()
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'sample-multiple-choice-question', SampleMultipleChoiceQuestionViewSet,
                basename='sample_multiple_choice_question')
router.register(r'user-consent', UserConsentViewSet, basename='user_consent')
router.register(r'contact-us', ContactUsViewSet, basename='contact_us')

app_name = 'api'
urlpatterns = router.urls
