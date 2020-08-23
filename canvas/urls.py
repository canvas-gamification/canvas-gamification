from django.urls import path

from canvas.views.views import course_list_view, course_view
from canvas.views.register_views import register_course_view

urlpatterns = [
    path('<int:pk>', course_view, name='course'),
    path('register/<int:pk>', register_course_view, name='course_register'),
    path('', course_list_view, name='course_list'),
]
app_name = 'canvas'
