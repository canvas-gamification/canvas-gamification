from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.serializers import CourseSerializer, CourseSerializerList
from api.permissions import CourseEditPermission, CourseCreatePermission
import api.error_messages as ERROR_MESSAGES
from canvas.models.models import CanvasCourse, MyUser, Event
from canvas.utils.utils import get_course_registration
from general.services.action import (
    course_registration_verify_action,
    course_registration_student_number_action,
    course_registration_confirm_name_action,
)


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Optional Parameters
    ?registered: boolean => if true, filter retrieved courses by if user is currently registered in them
    """

    serializer_class = CourseSerializer
    action_serializers = {
        "retrieve": CourseSerializer,
        "list": CourseSerializerList,
    }
    permission_classes = [CourseEditPermission, CourseCreatePermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "mock",
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

        if not user.is_authenticated or user.is_student:
            queryset = queryset.filter(visible_to_students=True).all()

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

    @action(detail=True, methods=["get"], url_path="get-registration-status")
    def get_registration_status(self, request, pk=None):
        """
        Returns the status of this logged-in user's course registration for a specific course.
        This is encoded as a string.
        """
        course = get_object_or_404(CanvasCourse, pk=pk)
        course_reg = get_course_registration(request.user, course)

        if course_reg.is_blocked:
            return Response(
                {
                    "status": "Blocked",
                    "message": "Registration has been blocked for you. Please contact your instructor.",
                    "attempts_remaining": course_reg.verification_attempts,
                }
            )

        if not course_reg.canvas_user_id:
            # if the CanvasCourseRegistration does not have a student number associated, then the user is not registered
            return Response(
                {
                    "status": "Not Registered",
                    "message": None,
                    "attempts_remaining": course_reg.verification_attempts,
                }
            )

        if not course_reg.is_verified:
            return Response(
                {
                    "status": "Awaiting Verification",
                    "message": None,
                    "attempts_remaining": course_reg.verification_attempts,
                }
            )
        else:
            return Response(
                {
                    "status": "Registered",
                    "message": "You have already successfully registered in this course!",
                    "attempts_remaining": course_reg.verification_attempts,
                }
            )

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
