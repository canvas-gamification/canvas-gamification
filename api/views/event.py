from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
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
        old_event_id = event.id
        event.id = None
        event.course = course
        event.save()
        for question in Question.objects.all().filter(event=old_event_id):
            question.id = None
            question.pk = None
            question.question_ptr_id = None
            question.event = event
            question.save()
        return Response({
            "success": True,
        })
