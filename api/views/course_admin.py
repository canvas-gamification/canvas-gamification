from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from accounts.models import MyUser
from api.permissions import TeacherAccessPermission
from api.serializers import CourseSerializer, CanvasCourseRegistrationSerializer
from canvas.models import CanvasCourse, CanvasCourseRegistration

import api.error_messages as ERROR_MESSAGES


class CourseAdminViewSet(viewsets.GenericViewSet):
    permission_classes = [TeacherAccessPermission, ]
    queryset = CanvasCourse.objects.all()
    serializer_class = CourseSerializer
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]

    @action(detail=True, methods=['get'], url_path='registered-users')
    def registered_users(self, request, pk=None):
        course = get_object_or_404(self.get_queryset(), pk=pk)
        course_registration_list = self.filter_queryset(course.canvascourseregistration_set.all())

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

        # TODO: Implement the registration that uses of canvas_user_id which can be done from canvas api

        return Response(request.data)

    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, pk=None):
        '''
        Action that will update the block/verify status of a canvascourseregistration object.
        '''
        registration_id = request.data.get("id")
        status = request.data.get("status")
        status_type = request.data.get("type")
        course_registration = get_object_or_404(CanvasCourseRegistration, id=registration_id)

        if status_type == "block":
            course_registration.is_blocked = status
            course_registration.save()

        if status_type == "verify":
            course_registration.is_verified = status
            course_registration.save()

        return Response(request.data)

    # TODO: Implement unregister_user function that will change is_blocked and is_verified into an enum. Fix other apis
