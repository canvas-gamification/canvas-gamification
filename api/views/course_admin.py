from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from accounts.models import MyUser
from api.permissions import TeacherAccessPermission
from api.serializers import CourseSerializer, CanvasCourseRegistrationSerializer
from canvas.models import CanvasCourse

import api.error_messages as ERROR_MESSAGES


class CourseAdminViewSet(viewsets.GenericViewSet):
    permission_classes = [TeacherAccessPermission, ]
    queryset = CanvasCourse.objects.all()
    serializer_class = CourseSerializer

    @action(detail=True, methods=['get'], url_path='registered-users')
    def registered_users(self, request, pk=None):
        course = get_object_or_404(self.get_queryset(), pk=pk)
        course_registration_list = course.canvascourseregistration_set.all()

        return Response(
            CanvasCourseRegistrationSerializer(course_registration).data
            for course_registration in course_registration_list
        )

    @action(detail=True, methods=['post'], url_path='register-user')
    def register_user(self, request, pk=None):
        course = get_object_or_404(self.get_queryset(), pk=pk)
        username = request.data.get('username', None)

        if not username:
            raise ValidationError(ERROR_MESSAGES.COURSE_REGISTRATION.USERNAME_REQUIRED)

        user = get_object_or_404(MyUser, username=username)

        if course.is_registered(user):
            raise ValidationError(ERROR_MESSAGES.COURSE_REGISTRATION.ALREADY_REGISTERED)

        # TODO: Implement the registration

        return Response(request.data)
