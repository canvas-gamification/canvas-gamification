from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from api.serializers.reset_password import ResetPasswordSerializer


class ResetPasswordViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, ]
    serializer_class = ResetPasswordSerializer
