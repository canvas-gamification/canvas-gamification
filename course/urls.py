from django.urls import path

from course.views import ProblemCreateView

urlpatterns = [
    path('new-problem', ProblemCreateView.as_view(), name='new_problem'),
]
