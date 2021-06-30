from django.urls import path

from . import views
from leader_board.views import leader_board_view

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:pk>', leader_board_view, name='leader_board'),
]