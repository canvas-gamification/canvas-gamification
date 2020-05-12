from django.urls import path

from api.views import QuestionViewSet

app_name = 'api'
urlpatterns = [
    path('problem-set', QuestionViewSet.as_view(), name='problem-set'),
]
