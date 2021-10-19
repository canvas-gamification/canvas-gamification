from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from api.serializers import ChangePasswordSerializer
from general.services.action import change_password_action


class ChangePasswordViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, ]
    serializer_class = ChangePasswordSerializer

    def perform_create(self, serializer):
        request = serializer.context['request']
        serializer.save()
        change_password_action(request.user)
