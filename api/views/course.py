from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.serializers import CourseSerializer, CourseSerializerList
from api.permissions import StudentsMustBeRegisteredPermission, CourseEditPermission, CourseCreatePermission
import api.error_messages as ERROR_MESSAGES
from canvas.models import CanvasCourse, MyUser
from canvas.utils.utils import get_course_registration
from general.services.action import course_registration_verify_action, course_registration_student_number_action, \
    course_registration_confirm_name_action


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Optional Parameters
    ?registered: boolean => if true, filter retrieved courses by if user is currently registered in them
    """
    serializer_class = CourseSerializer
    action_serializers = {
        'retrieve': CourseSerializer,
        'list': CourseSerializerList,
    }
    permission_classes = [StudentsMustBeRegisteredPermission, CourseEditPermission, CourseCreatePermission, ]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, ]
    filterset_fields = ['mock', 'name', 'allow_registration', 'visible_to_students', 'instructor', ]
    ordering_fields = ['name', 'start_date', 'end_date', ]

    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            return self.action_serializers.get(self.action, self.serializer_class)

        return super(CourseViewSet, self).get_serializer_class()

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        registered = self.request.query_params.get('registered', None)
        if registered:
            registered = registered.lower() == 'true'

        queryset = CanvasCourse.objects.all()

        if not user.is_authenticated or user.is_student:
            queryset = queryset.filter(visible_to_students=True).all()

        if registered:
            registered_ids = user.canvascourseregistration_set.filter(status='VERIFIED') \
                .values_list('course_id', flat=True)
            queryset = queryset.filter(pk__in=registered_ids)

        return queryset.all()

    @action(detail=True, methods=['get'], url_path="get-registration-status")
    def get_registration_status(self, request, pk=None):
        """
        Returns the status of this logged-in user's course registration for a specific course.
        This is encoded as a string.
        """
        course = get_object_or_404(CanvasCourse, pk=pk)
        course_reg = get_course_registration(request.user, course)

        if course_reg.is_blocked:
            return Response({
                "status": "Blocked",
                "message": "Registration has been blocked for you. Please contact your instructor.",
            })

        if not course_reg.canvas_user_id:
            # if the CanvasCourseRegistration does not have a student number associated, then the user is not registered
            return Response({
                "status": "Not Registered",
                "message": None,
            })

        if not course_reg.is_verified:
            return Response({
                "status": "Awaiting Verification",
                "message": None,
            })
        else:
            return Response({
                "status": "Registered",
                "message": None,
            })

    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        """
        This endpoint completes the 'next' stage of course registration for this (user, course) pair. It decides what
        the 'next' step is based on the status of the CanvasCourseRegistration and the request's POST data.
        - In each case, setting success = True lets the front-end know to advance the UI to the next stage.
        - Raising ValidationError() returns a pre-defined Response.
        """
        name = request.data.get("name", None)
        student_number = request.data.get("student_number", None)
        confirmed_name = request.data.get("confirmed_name", None)

        course = get_object_or_404(CanvasCourse, pk=pk)
        course_reg = get_course_registration(request.user, course)

        if student_number is not None:
            # if a student number was given in the request data, try to find this canvas user using it
            canvas_user = course.get_user(student_id=student_number)

            if canvas_user is None:
                raise ValidationError()

            course_reg.set_canvas_user(canvas_user)
            # Change status to PENDING-VERIFICATION after successfully find the user
            course_reg.unverify()
            course_registration_student_number_action(request.user)
            return Response({
                "success": True,
            })

        if confirmed_name is not None:
            # if a confirmed name was given in the request data, try to find this canvas user using it. The confirmed
            # name should be the same as the guessed name that the API responded with earlier in the process.
            canvas_user = course.get_user(name=confirmed_name)
            if not canvas_user:
                raise ValidationError(ERROR_MESSAGES.USER.INVALID)
            course_reg.set_canvas_user(canvas_user)
            # Change status to PENDING-VERIFICATION after successfully find the user
            course_reg.unverify()
            course_registration_confirm_name_action(request.user)
            return Response({
                "success": True,
            })

        if name is not None:
            # if an inputted name is in the request data, try to guess the name properly.
            guessed_names = course.guess_user(name)
            if len(guessed_names) == 0:
                raise ValidationError(ERROR_MESSAGES.USER.INVALID)
            elif len(guessed_names) > 1:
                # If more than 1 name is guessed, then the UI moves to the student number confirmation
                # since the student number confirmation is not the standard process, success = False lets the front-end
                # know what to render.
                return Response({
                    "success": False,
                    "guessed_name": None,
                })

            return Response({
                "success": True,
                "guessed_name": guessed_names[0],
            })

        raise ValidationError(ERROR_MESSAGES.USER.INVALID)

    @action(detail=True, methods=['post'], url_path="register-dashboard")
    def register_dashboard(self, request, pk=None):

        name = request.data.get("name", None)
        student_number = request.data.get("student_number", None)
        confirmed_name = request.data.get("confirmed_name", None)
        student_username = request.data.get("student_username", None)

        course = get_object_or_404(CanvasCourse, pk=pk)
        user = get_object_or_404(MyUser, username=student_username)
        course_reg = get_course_registration(user, course)

        if student_number is not None:
            # if a student number was given in the request data, try to find this canvas user using it
            canvas_user = course.get_user(student_id=student_number)

            if canvas_user is None:
                raise ValidationError()

            course_reg.set_canvas_user(canvas_user)
            course_reg.unverify()
            course_registration_student_number_action(user)
            return Response({
                "success": True,
            })
        if confirmed_name is not None:
            # if a confirmed name was given in the request data, try to find this canvas user using it. The confirmed
            # name should be the same as the guessed name that the API responded with earlier in the process.
            canvas_user = course.get_user(name=confirmed_name)
            if not canvas_user:
                raise ValidationError(ERROR_MESSAGES.USER.INVALID)
            course_reg.set_canvas_user(canvas_user)
            # Change status to PENDING-VERIFICATION after successfully find the user
            course_reg.unverify()
            course_registration_confirm_name_action(user)
            return Response({
                "success": True,
            })
        if name is not None:
            # if an inputted name is in the request data, try to guess the name properly.
            guessed_names = course.guess_user(name)
            if len(guessed_names) == 0:
                raise ValidationError(ERROR_MESSAGES.USER.INVALID)
            elif len(guessed_names) > 1:
                # If more than 1 name is guessed, then the UI moves to the student number confirmation
                # since the student number confirmation is not the standard process, success = False lets the front-end
                # know what to render.
                return Response({
                    "success": False,
                    "guessed_name": None,
                })

            return Response({
                "success": True,
                "guessed_name": guessed_names[0],
            })
        raise ValidationError(ERROR_MESSAGES.USER.INVALID)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        This endpoint completes the verification step of course registration.
        """
        code = request.data.get("code", None)

        if code is None:
            raise ValidationError(ERROR_MESSAGES.COURSE_REGISTRATION.INVALID_CODE)

        course = get_object_or_404(CanvasCourse, pk=pk)
        course_reg = get_course_registration(request.user, course)

        valid = course_reg.check_verification_code(code)
        course_registration_verify_action(request.user)
        return Response({
            "success": valid,
            "attempts_remaining": course_reg.verification_attempts,
        })

    @action(detail=True, methods=['get'], url_path='validate-event/(?P<event_pk>[^/.]+)')
    def validate_event(self, request, pk=None, event_pk=None):
        """
        Validates that an event belongs to a particular course.
        """
        course = get_object_or_404(CanvasCourse, pk=pk)

        if course is None:
            raise ValidationError(ERROR_MESSAGES.COURSE.INVALID)

        if course.events.filter(pk=event_pk).exists():
            return Response({
                "success": True
            })

        raise ValidationError(ERROR_MESSAGES.EVENT.INVALID)

    @action(detail=True, methods=['get'], url_path='user-stats/(?P<category_pk>[^/.]+)')
    def user_stats(self, request, pk=None, category_pk=None):
        """
        User stats.
        """
        success_rate = 0
        for pair in request.user.success_rate_by_category:
            if pair['category'] == int(category_pk):
                success_rate = pair['avgSuccess']
                break

        return Response({
            'success_rate': success_rate
        })
