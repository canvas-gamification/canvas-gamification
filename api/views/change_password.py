from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from api.serializers import ChangePasswordSerializer


class ChangePasswordViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, ]
    serializer_class = ChangePasswordSerializer
