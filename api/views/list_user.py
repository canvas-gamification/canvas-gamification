import django_filters
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from accounts.models import MyUser
from api.serializers import UsersCountSerializers


class MyFilterSet(FilterSet):
    canvascourseregistration__course__id__not = django_filters.NumberFilter(
        field_name='canvascourseregistration__course__id', exclude=True)

    class Meta:
        model = MyUser
        fields = []


class UsersCountViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['role']
    serializer_class = UsersCountSerializers
    filter_class = MyFilterSet
    search_fields = ['first_name', 'last_name', ]

    def get_queryset(self):
        return MyUser.objects
