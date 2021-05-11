from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import MyUser
from api.serializers import UserStatsSerializer


class UserStatsViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return MyUser.objects.filter(id=self.request.user.id)
    serializer_class = UserStatsSerializer
    permission_classes = [IsAuthenticated, ]
