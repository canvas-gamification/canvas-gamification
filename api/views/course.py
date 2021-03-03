from rest_framework import viewsets

from api.serializers import CourseSerializer
from canvas.models import CanvasCourse


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Optional Parameters
    ?registered: boolean => if true, filter retrieved courses by if user is currently registered in them
    """
    serializer_class = CourseSerializer

    def get_queryset(self):
        user = self.request.user
        registered = self.request.query_params.get('registered', None)
        if registered:
            registered = registered.lower() == 'true'

        queryset = CanvasCourse.objects.all()

        if not user.is_authenticated or user.is_student:
            queryset = queryset.filter(visible_to_students=True).all()

        if registered:
            registered_ids = user.canvascourseregistration_set.filter(is_verified=True, is_blocked=False)\
                .values_list('course_id', flat=True)
            queryset = queryset.filter(pk__in=registered_ids)

        return queryset.all()
