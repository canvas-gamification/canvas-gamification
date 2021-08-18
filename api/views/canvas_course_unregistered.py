from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from canvas.models import CanvasCourseRegistration
from canvas.models import CanvasCourse
from api.serializers import UsersCourseCountSerializers
from accounts.models import MyUser
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response


class CanvasCourseUnRegisteredViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    courses = CanvasCourseRegistration.objects.values('user__id')
    course_names = CanvasCourse.objects.values('name')
    queryset = MyUser.objects.all()

    filterset_fields = ['canvascourseregistration__course__id']

    serializer_class = UsersCourseCountSerializers

    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):

        user_id = request.data.get("id", None)
        user = MyUser.objects.get(id=user_id)
        course = get_object_or_404(CanvasCourse, pk=pk)
        course_reg = CanvasCourseRegistration(user=user, course=course)
        course_reg.save()

        if course_reg.is_blocked:
            return Response({
                "status": "Blocked",
                "message": "Registration has been blocked for this student. Please change the block status.",
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

        raise ValidationError(ERROR_MESSAGES.USER.INVALID)
