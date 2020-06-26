from django.urls import path

from course.views.views import problem_set_view, question_view, multiple_choice_question_create_view, \
    checkbox_question_create_view, java_question_create_view, submission_detail_view, token_values_table_view, \
    question_edit_view, parsons_question_create_view

urlpatterns = [
    path('new-problem/multiple-choice', multiple_choice_question_create_view, name='new_problem_multiple_choice'),
    path('new-problem/checkbox', checkbox_question_create_view, name='new_problem_checkbox'),
    path('new-problem/java', java_question_create_view, name='new_problem_java'),
    path('new-problem/parsons', parsons_question_create_view, name='new_problem_parsons'),
    path('submission/<int:pk>', submission_detail_view, name='submission_detail'),
    path('question/<int:pk>/edit', question_edit_view, name='question_edit'),
    path('question/<int:pk>/', question_view, name='question_view'),
    path('problem-set', problem_set_view, name='problem_set'),
    path('token-values', token_values_table_view, name='token_values'),
]
