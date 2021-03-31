from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers import EventSerializer
from canvas.models import Event
from canvas.models import EVENT_TYPE_CHOICES


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

    @action(detail=False, methods=['get'], url_path="get-event-types")
    def get_event_types(self, request):
        event_types = [value for (key,value) in EVENT_TYPE_CHOICES]
        return Response({
            "event_types": event_types,
        })

    def get_queryset(self):
        return Event.objects.all()
