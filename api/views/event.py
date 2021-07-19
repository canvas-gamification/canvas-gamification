from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.permissions import IsOwnerOrReadOnly
from api.serializers import EventSerializer
from canvas.models import Event, EVENT_TYPE_CHOICES, CanvasCourse
from course.models.models import Question


class EventViewSet(viewsets.ModelViewSet):
    """
    Optional Parameters
    - Base filtering on the 'course' parameter
    """
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, ]
    filter_backends = [DjangoFilterBackend, ]
    filterset_fields = ['course', ]

    def get_queryset(self):
        return Event.objects.all()

    @action(detail=False, methods=['get'], url_path="get-event-types")
    def get_event_types(self, request, pk=None):
        """
        Returns a dictionary of the defined event types
        """
        return Response(EVENT_TYPE_CHOICES)

    @action(detail=False, methods=['post'], url_path="duplicate-event")
    def duplicate_event(self, request):
        """
        Duplicates an event as well as the questions within the event.
        """
        event = Event.objects.filter(id=request.data.get("event", None)).first()
        course = CanvasCourse.objects.filter(id=request.data.get("course", None)).first()
        current_author = None
        if request.user.is_authenticated:
            current_author = request.user
        if event and course:
            old_event_id = event.id
            event.clone(course)
            for question in Question.objects.all().filter(event=old_event_id):
                question.clone(course, event, current_author)
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND, data='The event or course provided could not be found.')
