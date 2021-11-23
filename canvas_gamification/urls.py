import os

from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from graphene_django.views import GraphQLView

from api.schema import schema
from canvas_gamification import views
from canvas_gamification.views import angular
from general.views import faq

if settings.DEBUG:
    urlpatterns = [
        path('admin/', admin.site.urls),
        path('djrichtextfield/', include('djrichtextfield.urls')),
        path('accounts/', include(('accounts.urls', 'accounts'))),
        path('course/', include(('course.urls', 'course'))),
        path('faq/', faq, name='faq'),
        path('homepage/', views.homepage, name='homepage'),
        path('actions/', views.action_view, name='actions'),
        path('terms-and-conditions/', TemplateView.as_view(template_name='terms_and_conditions.html'),
             name='terms_and_conditions'),
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
        path('api/', include('api.urls', namespace='api')),
        path('graphql', csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
        path('canvas/', include('canvas.urls', namespace='canvas')),
        path('', TemplateView.as_view(template_name='index.html')),
    ]
else:
    urlpatterns = [
        path('admin/', admin.site.urls),
        path('api/', include('api.urls', namespace='api')),
        path('djrichtextfield/', include('djrichtextfield.urls')),
        path('', angular, {'document_root': os.path.join(settings.BASE_DIR, 'static', 'angular')}),
        path('<path:path>', angular, {'document_root': os.path.join(settings.BASE_DIR, 'static', 'angular')}),
    ]
