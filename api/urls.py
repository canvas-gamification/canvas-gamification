from rest_framework.routers import DefaultRouter

from api.views import QuestionViewSet, MultipleChoiceQuestionViewSet

router = DefaultRouter()
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'multiple-choice-question', MultipleChoiceQuestionViewSet, basename='multiple_choice_question')

app_name = 'api'
urlpatterns = router.urls