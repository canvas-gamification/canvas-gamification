from api.filters import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.permissions import (
    IsOwnerOrReadOnly,
    EventCreatePermission,
    EventEditPermission,
    is_course_member,
)
from api.serializers import EventSerializer
from canvas.models.models import Event, EVENT_TYPE_CHOICES, CanvasCourse, CHALLENGE_TYPE_CHOICES
from canvas.services.event import get_event_stats, set_featured, add_question_set, clear_featured
from course.models.models import Question
from course.services.question import get_number_of_questions_counted_by_category_and_difficulty
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
        event = serializer.save(author=request.user)
        create_event_action(request.user, serializer.data)

    def perform_update(self, serializer):
        request = serializer.context["request"]
        serializer.save()
        update_event_action(request.user, serializer.data)

    # The detail actions below go through ``self.get_object()`` so that
    # ``IsOwnerOrReadOnly`` (edit permission on the event) is enforced. A bare
    # ``get_object_or_404`` would skip every object-level permission.

    @action(detail=True, methods=["post"], url_path="add-question-set")
    def add_question_set(self, request, pk=None):
        event = self.get_object()
        category = request.data.get("category", None)
        difficulty = request.data.get("difficulty", None)
        number_of_questions = request.data.get("number_of_questions", None)

        add_question_set(event, category, difficulty, number_of_questions)
        return Response("success")

    @action(detail=True, methods=["post"], url_path="add-question")
    def add_question(self, request, pk=None):
        event = self.get_object()
        question_id = request.data.get("question_id")
        question = get_object_or_404(Question, id=question_id)
        # Copying a question also copies its answer, so the source must be one the
        # caller is allowed to see in full.
        if not question.is_practice and not question.has_edit_permission(request.user):
            raise PermissionDenied()
        question.copy_to_event(event)
        return Response("success")

    @action(detail=True, methods=["post"], url_path="remove-question")
    def remove_question(self, request, pk=None):
        event = self.get_object()
        question_id = request.data.get("question_id")
        question = get_object_or_404(Question, id=question_id, event_id=event.id)
        question.soft_delete()

        return Response("success")

    @action(detail=True, methods=["get"], url_path="stats")
    def stats(self, request, pk=None):
        event = self.get_object()
        # Stats expose every student's submissions; GET is "safe" for
        # IsOwnerOrReadOnly, so the edit check has to be explicit here.
        if not event.has_edit_permission(request.user):
            raise PermissionDenied()
        return Response(get_event_stats(event))

    @action(detail=True, methods=["post"], url_path="set-featured")
    def set_featured(self, request, pk=None):
        event = self.get_object()
        set_featured(event)
        return Response("success")

    @action(detail=True, methods=["post"], url_path="clear-featured")
    def clear_featured(self, request, pk=None):
        event = self.get_object()
        clear_featured(event)
        return Response("success")

    @action(detail=False, methods=["get"], url_path="get-event-types")
    def get_event_types(self, request):
        """
        Returns a dictionary of the defined event types
        """
        return Response(EVENT_TYPE_CHOICES)

    @action(detail=False, methods=["get"], url_path="get-challenge-types")
    def get_challenge_types(self, request, pk=None):
        """
        Returns a dictionary of the defined challenge types
        """
        return Response(CHALLENGE_TYPE_CHOICES)

    @action(detail=False, methods=["post"], url_path="import-event")
    def import_event(self, request):
        """
        Duplicates an event as well as the questions within the event.
        """
        event = get_object_or_404(Event, id=request.data.get("event"))
        course = get_object_or_404(CanvasCourse, id=request.data.get("course"))
        # Only the target course is checked (EventCreatePermission). The UI's import
        # dialog deliberately offers events from every course, so the source event
        # is not restricted here.
        cloned_event = event.copy_to_course(course)

        import_event_action(request.user, self.get_serializer(cloned_event).data)
        return Response(
            self.get_serializer(cloned_event).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="leader-board")
    def leader_board(self, request, pk):
        """
        Given event id, return the event leader board.
        """
        event = self.get_object()
        if not is_course_member(request.user, event.course):
            raise PermissionDenied()
        leader_board = [
            {
                "name": team.name,
                "token": team.tokens_received,
                "member_names": team.member_names,
                "team_id": team.id,
            }
            for team in event.team_set.all()
            if team.course_registrations.filter(status="VERIFIED", registration_type="STUDENT").exists()
        ]

        return Response(leader_board)

    @action(detail=False, methods=["get"], url_path="limits")
    def limits(self, request):
        result = get_number_of_questions_counted_by_category_and_difficulty()
        return Response(result)
