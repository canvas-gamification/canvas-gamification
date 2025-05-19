import csv

from django.db.models import Prefetch, Q
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from accounts.utils.email_functions import course_create_email
from api.serializers import CourseSerializer, CourseListSerializer, CanvasCourseRegistrationSerializer
from api.permissions import CoursePermission, GradeBookPermission, StudentsMustBeRegisteredPermission
import api.error_messages as ERROR_MESSAGES
from api.serializers.course import CourseCreateSerializer

from api.serializers.eventSet import EventSetSerializer
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
        "edit": CourseCreateSerializer,
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
        for event in events_sort:
            event.update_featured()
        prefetch = Prefetch("events", queryset=events_sort)
        queryset.prefetch_related(prefetch)

        return queryset.all()

    def perform_create(self, serializer):
        request = serializer.context["request"]
        course = serializer.save(instructor=request.user)
        course_create_email(course)
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
                "course_reg_id": course_reg.id,
            }
            for course_reg in course.canvascourseregistration_set.filter(
                status="VERIFIED", registration_type="STUDENT"
            ).all()
        ]

        return Response(leader_board)

    @action(detail=True, methods=["get"], url_path="course-event-sets")
    def course_event_sets(self, request, pk):
        """
        Given course id, return all event-sets within a course
        """
        course = get_object_or_404(CanvasCourse, id=pk)

        event_sets = EventSetSerializer(course.eventSets, many=True)

        return Response(event_sets.data)

    @action(detail=True, methods=["get"], url_path="my-grades", permission_classes=[StudentsMustBeRegisteredPermission])
    def my_grades(self, request, pk):
        course = self.get_object()
        students = course.verified_course_registration.filter(registration_type="STUDENT", user=request.user)
        if students.count() == 0:
            raise ValueError(ERROR_MESSAGES.TOKEN_USE.NO_STUDENT_GRADES_FOUND)
        student = students[0]
        results = []

        for event in course.events.filter(type__in=["ASSIGNMENT", "EXAM"]):
            uqjs = student.user.question_junctions.filter(question__event_id__in=[event.id])
            results.append(
                {
                    "grade": sum(uqjs.values_list("tokens_received", flat=True)),
                    "total": event.total_tokens,
                    "name": student.full_name,
                    "event_name": event.name,
                    "question_details": [
                        {
                            "title": uqj.question.title,
                            "question_grade": uqj.formatted_current_tokens_received,
                            "attempts": uqj.submissions.count(),
                            "max_attempts": uqj.question.max_submission_allowed,
                        }
                        for uqj in uqjs
                    ],
                }
            )
        return Response(results)

    @action(detail=True, methods=["get"], url_path="grade-book", permission_classes=[GradeBookPermission])
    def course_grade_book(self, request, pk, response=True):
        course = self.get_object()
        students = course.verified_course_registration.filter(registration_type="STUDENT")
        results = []

        for event in course.events.filter(type__in=["ASSIGNMENT", "EXAM"]):
            for student in students:
                uqjs = student.user.question_junctions.filter(question__event_id__in=[event.id])
                results.append(
                    {
                        "grade": sum(uqjs.values_list("tokens_received", flat=True)),
                        "total": event.total_tokens,
                        "name": student.full_name,
                        "event_name": event.name,
                        "question_details": [
                            {
                                "title": uqj.question.title,
                                "question_grade": uqj.formatted_current_tokens_received,
                                "attempts": uqj.submissions.count(),
                                "max_attempts": uqj.question.max_submission_allowed,
                            }
                            for uqj in uqjs
                        ],
                    }
                )
        if response:
            return Response(results)
        return results

    @action(detail=True, methods=["get"], url_path="export-grade-book", permission_classes=[GradeBookPermission])
    def export_grade_book(self, request, pk):
        """
        Optional Parameters:\n
        ?event_name: string => filters retrieved grades by the event\n
        ?student_name: string => filters retrieved grades by students whose name is a full or partial match\n
        ?details: boolean => if true, adds question level breakdown to each overall event grade
        """
        event_name = request.GET.get('event_name', '')
        student_name = request.GET.get('student_name', '')
        details = request.GET.get('details', 'false')

        response = HttpResponse(
            content_type="text/csv"
        )

        response["Content-Disposition"] = f'attachment; filename="{self.get_object().name} ' \
                                          f'{"" if student_name == "" else student_name + " students "}' \
                                          f'{"course" if event_name == "" else event_name} ' \
                                          f'gradebook{" detailed" if details == "true" else ""}.csv"'
        csv_data = self.course_grade_book("request", "pk", False)

        if event_name != '' and event_name is not None:
            csv_data = filter(lambda gb: gb["event_name"] == event_name, csv_data)

        if student_name != '' and student_name is not None:
            csv_data = filter(lambda gb: student_name.lower() in gb["name"].lower(), csv_data)

        writer = csv.writer(response)
        row = ["Event Name", "Student Name", "Grade", "Total", "Question Title", "Question Grade", "Attempts",
               "Max Attempts"] if details == "true" else ["Event Name", "Student Name", "Grade", "Total"]
        writer.writerow(row)

        for student_event_grade in csv_data:
            if details != "true":
                writer.writerow([student_event_grade["event_name"], student_event_grade["name"],
                                 student_event_grade["grade"], student_event_grade["total"]])
            if details == "true":
                writer.writerow([student_event_grade["event_name"], student_event_grade["name"],
                                 student_event_grade["grade"], student_event_grade["total"],
                                 student_event_grade["question_details"][0]["title"],
                                 student_event_grade["question_details"][0]["question_grade"],
                                 student_event_grade["question_details"][0]["attempts"],
                                 student_event_grade["question_details"][0]["max_attempts"]])
                for question_detail in student_event_grade["question_details"][1:]:
                    writer.writerow(["", "", "", "", question_detail["title"], question_detail["question_grade"],
                                     question_detail["attempts"], question_detail["max_attempts"]])

        return response
