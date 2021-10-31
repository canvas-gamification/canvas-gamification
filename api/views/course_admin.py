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
from general.services.action import course_registration_update_action, course_registration_create_action

import api.error_messages as ERROR_MESSAGES


class CourseAdminViewSet(viewsets.GenericViewSet):
    permission_classes = [TeacherAccessPermission, ]
    queryset = CanvasCourse.objects.all()
    serializer_class = CourseSerializer
    ordering_fields = ['id', 'user__username', 'user__first_name', 'status']
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]

    @action(detail=True, methods=['get'], url_path='registered-users')
    def registered_users(self, request, pk=None):
        course = get_object_or_404(self.get_queryset(), pk=pk)
        name = request.query_params.get('search', '')
        course_registration_list = self.filter_queryset(course.canvascourseregistration_set.all())
        # Filter courseregistration based on first name or last name
        first_name_filter = course_registration_list.filter(user__first_name__contains=name)
        last_name_filter = course_registration_list.filter(user__last_name__contains=name)
        course_registration_list = first_name_filter | last_name_filter

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
        canvascourseregistration = CanvasCourseRegistration(course=course, user=user)
        canvascourseregistration.save()

        # Call and save actions
        serialized_courseregistration = CanvasCourseRegistrationSerializer(canvascourseregistration).data
        course_registration_create_action(serialized_courseregistration, self.request.user)

        return Response(request.data)

    @action(detail=False, methods=['post'], url_path='change-status')
    def update_status(self, request):
        '''
        Action that will update the status of a canvascourseregistration object.
        '''
        registration_id = request.data.get("id")
        status = request.data.get("status")
        # Get the object and update its is_block and is_verified
        course_registration = get_object_or_404(CanvasCourseRegistration, id=registration_id)
        if status == 'VERIFIED':
            course_registration.verify()
        if status == 'BLOCKED':
            course_registration.block()
        if status == 'PENDING_VERIFICATION':
            course_registration.unverify()
        if status == 'UNREGISTERED':
            course_registration.unregister()

        course_registration.save()

        # Call and save actions
        data = {status: status}
        course_registration_update_action(course_registration, self.request.user, data)
        return Response(request.data)
