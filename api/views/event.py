from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.permissions import (
    IsOwnerOrReadOnly,
    EventCreatePermission,
    EventEditPermission,
)
from api.serializers import EventSerializer
from canvas.models.models import Event, EVENT_TYPE_CHOICES, CanvasCourse
from canvas.services.event import get_event_stats
from general.services.action import (
    create_event_action,
    update_event_action,
    import_event_action,
)


class EventViewSet(viewsets.ModelViewSet):
    """
    Optional Parameters
    - Base filtering on the 'course' parameter
    """

    serializer_class = EventSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwnerOrReadOnly,
        EventCreatePermission,
        EventEditPermission,
    ]
    filter_backends = [
        DjangoFilterBackend,
    ]
    filterset_fields = [
        "course",
    ]

    def get_queryset(self):
        return Event.objects.all()

    def perform_create(self, serializer):
        request = serializer.context["request"]
        serializer.save()
        create_event_action(request.user, serializer.data)

    def perform_update(self, serializer):
        request = serializer.context["request"]
        serializer.save()
        update_event_action(request.user, serializer.data)

    @action(detail=True, methods=['get'], url_path="stats")
    def stats(self, request, pk=None):
        event = get_object_or_404(Event, id=pk)
        return Response(get_event_stats(event))

    @action(detail=False, methods=["get"], url_path="get-event-types")
    def get_event_types(self, request):
        """
        Returns a dictionary of the defined event types
        """
        return Response(EVENT_TYPE_CHOICES)

    @action(detail=False, methods=["post"], url_path="import-event")
    def import_event(self, request):
        """
        Duplicates an event as well as the questions within the event.
        """
        event = get_object_or_404(Event, id=request.data.get("event"))
        course = get_object_or_404(CanvasCourse, id=request.data.get("course"))
        cloned_event = event.copy_to_course(course)

        import_event_action(request.user, self.get_serializer(cloned_event).data)
        return Response(
            self.get_serializer(cloned_event).data,
            status=status.HTTP_201_CREATED,
        )
