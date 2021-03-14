from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers import CourseSerializer
from canvas.models import CanvasCourse, CanvasCourseRegistration
from canvas.utils.utils import get_course_registration


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Optional Parameters
    ?registered: boolean => if true, filter retrieved courses by if user is currently registered in them
    """
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['mock', 'name', 'allow_registration', 'visible_to_students', 'instructor']
    ordering_fields = ['name', 'start_date', 'end_date', ]

    def get_queryset(self):
        user = self.request.user
        registered = self.request.query_params.get('registered', None)
        if registered:
            registered = registered.lower() == 'true'

        queryset = CanvasCourse.objects.all()

        if not user.is_authenticated or user.is_student:
            queryset = queryset.filter(visible_to_students=True).all()

        if registered:
            registered_ids = user.canvascourseregistration_set.filter(is_verified=True, is_blocked=False) \
                .values_list('course_id', flat=True)
            queryset = queryset.filter(pk__in=registered_ids)

        return queryset.all()

    @action(detail=True, methods=['get'], url_path="get-registration-status")
    def get_registration_status(self, request, pk=None):
        course = get_object_or_404(CanvasCourse, pk=pk)
        course_reg = get_course_registration(request.user, course)

        if course_reg is None:
            course_reg = CanvasCourseRegistration(user=request.user, course=course)
            course_reg.save()

        if course_reg.is_blocked:
            return Response({
                "status": "Blocked",
                "message": "Registration has been blocked for you. Please contact your instructor.",
            })

        if not course_reg.canvas_user_id:
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
        name = request.POST.get("name", None)
        student_number = request.POST.get("student_number", None)
        confirmed_name = request.POST.get("confirmed_name", None)

        course = get_object_or_404(CanvasCourse, pk=pk)
        course_reg = get_course_registration(request.user, course)

        if course_reg is None:
            course_reg = CanvasCourseRegistration(user=request.user, course=course)
            course_reg.save()

        if student_number is not None:
            canvas_user = course.get_user(student_id=student_number)

            if canvas_user is None:
                raise ValidationError()

            course_reg.set_canvas_user(canvas_user)
            return Response({
                "success": True,
            })

        if confirmed_name is not None:
            canvas_user = course.get_user(name=confirmed_name)
            if not canvas_user:
                raise ValidationError()
            course_reg.set_canvas_user(canvas_user)
            return Response({
                "success": True,
            })

        if name is not None:
            guessed_names = course.guess_user(name)
            if len(guessed_names) == 0:
                raise ValidationError()
            elif len(guessed_names) > 1:
                return Response({
                    "success": False,
                    "guessed_name": None,
                })

            return Response({
                "success": False,
                "guessed_name": guessed_names[0],
            })

        raise ValidationError()

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        code = request.POST.get("code", None)

        if code is None:
            raise ValidationError()

        course = get_object_or_404(CanvasCourse, pk=pk)
        course_reg = get_course_registration(request.user, course)

        if course_reg is None:
            raise ValidationError()

        valid = course_reg.check_verification_code(code)
        return Response({
            "success": valid,
            "attempts_remaining": course_reg.verification_attempts,
        })
