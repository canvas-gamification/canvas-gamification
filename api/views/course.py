from django.db.models import Prefetch, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.serializers import CourseSerializer, CourseListSerializer, CanvasCourseRegistrationSerializer
from api.permissions import CoursePermission
import api.error_messages as ERROR_MESSAGES
from api.serializers.course import CourseCreateSerializer
from canvas.models.models import CanvasCourse, Event
from canvas.services.course import register_instructor
from canvas.utils.utils import get_course_registration


class CourseViewSet(viewsets.ModelViewSet):
    """
    Optional Parameters
    ?registered: boolean => if true, filter retrieved courses by if user is currently registered in them
    """

    serializer_class = CourseSerializer
    action_serializers = {
        "retrieve": CourseSerializer,
        "list": CourseListSerializer,
        "create": CourseCreateSerializer,
    }
    permission_classes = [CoursePermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "name",
        "allow_registration",
        "visible_to_students",
        "instructor",
    ]
    ordering_fields = [
        "name",
        "start_date",
        "end_date",
    ]

    def get_serializer_class(self):
        if hasattr(self, "action_serializers"):
            return self.action_serializers.get(self.action, self.serializer_class)

        return super(CourseViewSet, self).get_serializer_class()

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        registered = self.request.query_params.get("registered", None)
        if registered:
            registered = registered.lower() == "true"

        queryset = CanvasCourse.objects.all()

        if user.is_student:
            queryset = queryset.filter(Q(visible_to_students=True) | Q(instructor=user)).all()

        if registered:
            registered_ids = user.canvascourseregistration_set.filter(status="VERIFIED").values_list(
                "course_id", flat=True
            )
            queryset = queryset.filter(pk__in=registered_ids)

        # Sort the events based on time
        events_sort = Event.objects.all().order_by("start_date")
        prefetch = Prefetch("events", queryset=events_sort)
        queryset.prefetch_related(prefetch)

        return queryset.all()

    def perform_create(self, serializer):
        request = serializer.context["request"]
        course = serializer.save(instructor=request.user)
        register_instructor(request.user, course)

    @action(detail=True, methods=["post"], url_path="register")
    def register(self, request, pk=None):
        code = request.data.get("code", None)
        course = get_object_or_404(CanvasCourse, pk=pk)
        course_reg = get_course_registration(request.user, course)

        if course.registration_mode == "OPEN" or code == course.registration_code:
            course_reg.verify()
            course_reg.save()
            return Response(self.get_serializer(course).data)
        raise ValidationError(ERROR_MESSAGES.COURSE_REGISTRATION.INVALID_CODE)

    @action(
        detail=True,
        methods=["get"],
        url_path="validate-event/(?P<event_pk>[^/.]+)",
    )
    def validate_event(self, request, pk=None, event_pk=None):
        """
        Validates that an event belongs to a particular course.
        """
        course = get_object_or_404(CanvasCourse, pk=pk)

        if course is None:
            raise ValidationError(ERROR_MESSAGES.COURSE.INVALID)

        if course.events.filter(pk=event_pk).exists():
            return Response({"success": True})

        raise ValidationError(ERROR_MESSAGES.EVENT.INVALID)

    @action(
        detail=True,
        methods=["get"],
        url_path="user-stats/(?P<category_pk>[^/.]+)",
    )
    def user_stats(self, request, pk=None, category_pk=None):
        """
        User stats.
        """
        success_rate = 0
        for pair in request.user.success_rate_by_category:
            if pair["category"] == int(category_pk):
                success_rate = pair["avgSuccess"]
                break

        return Response({"success_rate": success_rate})

    @action(detail=True, methods=["get"], url_path="course-registrations")
    def course_registrations(self, request, pk):
        """
        Given course id, return all students within a class
        """
        course = get_object_or_404(CanvasCourse, id=pk)

        course_regs = CanvasCourseRegistrationSerializer(course.verified_course_registration, many=True)

        return Response(course_regs.data)

    @action(detail=True, methods=["get"], url_path="leader-board")
    def leader_board(self, request, pk):
        """
        Given course id, return the leader board for the course.
        """
        course = get_object_or_404(CanvasCourse, id=pk)
        leader_board = [
            {
                "name": course_reg.user.get_full_name(),
                "token": course_reg.total_tokens_received,
            }
            for course_reg in course.canvascourseregistration_set.all().filter(status="VERIFIED").all()
        ]

        return Response(leader_board)
