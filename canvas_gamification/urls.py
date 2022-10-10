"""canvas_gamification URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os

from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from canvas_gamification.views import angular

if settings.DEBUG:
    urlpatterns = [
        path("admin/", admin.site.urls),
        path(
            "api-auth/",
            include("rest_framework.urls", namespace="rest_framework"),
        ),
        path("api/", include("api.urls", namespace="api")),
    ]
else:
    urlpatterns = [
        path("admin/", admin.site.urls),
        path("api/", include("api.urls", namespace="api")),
        path(
            "",
            angular,
            {"document_root": os.path.join(settings.BASE_DIR, "static", "angular")},
        ),
        path(
            "<path:path>",
            angular,
            {"document_root": os.path.join(settings.BASE_DIR, "static", "angular")},
        ),
    ]
