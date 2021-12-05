from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import MyUser
from api.serializers import UpdateProfileSerializer
from general.services.action import update_user_profile_action


class UpdateProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UpdateProfileSerializer
    permission_classes = [IsAuthenticated, ]

    def get_queryset(self):
        return MyUser.objects.filter(id=self.request.user.id)

    def perform_update(self, serializer):
        request = serializer.context['request']
        serializer.save()
        update_user_profile_action(request.user, request.data)
