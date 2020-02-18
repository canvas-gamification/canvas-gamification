from django.urls import path

from course.views import ProblemCreateView, problem_set_view, question_view

urlpatterns = [
    path('new-problem', ProblemCreateView.as_view(), name='new_problem'),
    path('question/<int:pk>/', question_view, name='question_view'),
    path('problem-set', problem_set_view, name='problem_set'),
]
