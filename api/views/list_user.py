from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from accounts.models import MyUser
from api.serializers import UsersCountSerializers


class UsersCountViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['role']

    def get_queryset(self):
        return MyUser.objects

    serializer_class = UsersCountSerializers
