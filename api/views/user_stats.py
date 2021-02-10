from rest_framework import viewsets

from accounts.models import MyUser
from api.serializers import UserStatsSerializer


class UserStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MyUser.objects.all()
    serializer_class = UserStatsSerializer