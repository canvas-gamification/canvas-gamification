from django.urls import path

from course.views import problem_set_view, question_view, multiple_choice_question_create_view

urlpatterns = [
    path('new-problem', multiple_choice_question_create_view, name='new_problem'),
    path('question/<int:pk>/', question_view, name='question_view'),
    path('problem-set', problem_set_view, name='problem_set'),
]
