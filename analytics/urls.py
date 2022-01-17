from django.urls import path
from . import views

urlpatterns = [
    path('submission-analytics', views.analysis),
] 
