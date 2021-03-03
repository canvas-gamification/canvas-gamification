from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from api.serializers import CanvasCourseRegistrationSerializer
from canvas.models import CanvasCourseRegistration


class CanvasCourseRegistrationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Optional Parameters
    - Base filtering on the 'course' parameter
    """
    serializer_class = CanvasCourseRegistrationSerializer
    filter_backends = [DjangoFilterBackend, ]
    filterset_fields = ['course', ]

    def get_queryset(self):
        user = self.request.user
        return CanvasCourseRegistration.objects.filter(user=user).all()

