from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.permissions import TeacherAccessPermission
from api.serializers import CourseSerializer, CanvasCourseRegistrationSerializer
from canvas.models import CanvasCourse, CanvasCourseRegistration
from general.services.action import course_registration_update_action


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
