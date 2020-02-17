from django.urls import path

from course.views import ProblemCreateView, multiple_choice_question_view

urlpatterns = [
    path('new-problem', ProblemCreateView.as_view(), name='new_problem'),
    path('multiple-choice-question/<int:pk>/', multiple_choice_question_view, name='multiple_choice_question')
]
