from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from canvas.models import CanvasCourseRegistration
from canvas.models import CanvasCourse
from api.serializers import UsersCourseCountSerializers
from accounts.models import MyUser


class UsersCourseCountViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    courses = CanvasCourseRegistration.objects.values('user__id')
    course_names = CanvasCourse.objects.values('name')
    queryset = MyUser.objects.filter(id__in=courses)

    search_fields = ['first_name', 'last_name', ]
    filterset_fields = ['role', 'canvascourseregistration__course__name', 'canvascourseregistration__course__id']

    serializer_class = UsersCourseCountSerializers
