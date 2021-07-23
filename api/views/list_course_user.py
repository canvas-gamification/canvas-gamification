from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from canvas.models import CanvasCourseRegistration
from canvas.models import CanvasCourse
from api.serializers import UsersCourseCountSerializers
from accounts.models import MyUser


class UsersCourseCountViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['role']
    def get_queryset(self):
        courses = CanvasCourseRegistration.objects.values('user_id')
        users = MyUser.objects.filter(id__in=courses).annotate(course_in=CanvasCourse.objects.filter(course_id__in=CanvasCourseRegistration.objects.filter(user_id=1).values('course_id')).values('name'))
        return users

    serializer_class = UsersCourseCountSerializers


