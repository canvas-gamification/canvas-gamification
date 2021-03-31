from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from api.serializers import EventSerializer
from canvas.models import Event


class EventViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.DestroyModelMixin, mixins.UpdateModelMixin,
                   mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Optional Parameters
    - Base filtering on the 'course' parameter
    """
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend, ]
    filterset_fields = ['course', ]

    def get_queryset(self):
        return Event.objects.all()
