from django.urls import path

from canvas.views.register_views import register_course_view
from canvas.views.views import course_list_view, course_view, event_problem_set, events_options_view

urlpatterns = [
    path('<int:pk>', course_view, name='course'),
    path('<int:pk>/register', register_course_view, name='course_register'),
    path('events-options', events_options_view, name='course_events_options'),
    path('event/<int:event_id>/problem-set', event_problem_set, name='event_problem_set'),
    path('', course_list_view, name='course_list'),
]
app_name = 'canvas'
