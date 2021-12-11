from django.urls import path
from . import views

urlpatterns = [
    path('question-analytics', views.question_analytics),
    path('submission-analytics', views.submission_analytics),
]
