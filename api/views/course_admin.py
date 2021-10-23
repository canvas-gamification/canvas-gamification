from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from accounts.models import MyUser
from api.permissions import TeacherAccessPermission
from api.serializers import CourseSerializer, CanvasCourseRegistrationSerializer
from canvas.models import CanvasCourse, CanvasCourseRegistration

import api.error_messages as ERROR_MESSAGES


class CourseAdminViewSet(viewsets.GenericViewSet):
    permission_classes = [TeacherAccessPermission, ]
    queryset = CanvasCourse.objects.all()
    serializer_class = CourseSerializer

    @action(detail=True, methods=['get'], url_path='registered-users')
    def registered_users(self, request, pk=None):
        course = get_object_or_404(self.get_queryset(), pk=pk)
        name = request.query_params.get('search', '')
        course_registration_list = course.canvascourseregistration_set.all()
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

        user = MyUser.objects.all().filter(username=username).get()

        if course.is_registered(user):
            raise ValidationError(ERROR_MESSAGES.COURSE_REGISTRATION.ALREADY_REGISTERED)

        # TODO: Implement the registration that uses of canvas_user_id which can be done from canvas api
        canvascourseregistration = CanvasCourseRegistration(course=course, user=user)
        canvascourseregistration.save()

        return Response(request.data)

    @action(detail=False, methods=['post'], url_path='change-status')
    def update_registration(self, request):
        '''
        Action that will update the status of a canvascourseregistration object.
        '''
        registration_id = request.data.get("id")
        status = request.data.get("status")
        # Get the object and update its is_block and is_verified
        course_registration = get_object_or_404(CanvasCourseRegistration, id=registration_id)

        if status == 'Verified':
            course_registration.status = "VERIFIED"
        if status == 'Blocked':
            course_registration.status = "BLOCKED"

        course_registration.save()

        return Response(request.data)

    # TODO: Implement unregister_user function that will change is_blocked and is_verified into an enum. Fix other apis
    @action(detail=False, methods=['post'], url_path='unregister-user')
    def unregister_user(self, request):
        '''
        Action that will change the status of  a canvascourseregistration object to unregistered.
        '''
        registration_id = request.data.get("id")
        status = request.data.get("register_status")
        # Get the object and update its is_block and is_verified
        course_registration = get_object_or_404(CanvasCourseRegistration, id=registration_id)
        if status == 'Registered':
            course_registration.status = "UNREGISTERED"
        if status == 'Unregistered':
            course_registration.status = "PENDING_VERIFICATION"

        # TODO: Implement the registration that uses of canvas_user_id which can be done from canvas api
        course_registration.save()

        return Response(request.data)
