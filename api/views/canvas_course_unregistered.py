from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from api.serializers import CanvasCourseUnRegisteredSerializer
from accounts.models import MyUser
from canvas.models import CanvasCourseRegistration


class CanvasCourseUnRegisteredViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Optional Parameters
    - Base filtering on the 'course' parameter
    """
    serializer_class = CanvasCourseUnRegisteredSerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend, ]
    filterset_fields = ['course', ]

    def get_queryset(self):
        user = self.request.user
        return MyUser.objects
