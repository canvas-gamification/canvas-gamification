from rest_framework import mixins, viewsets

from accounts.models import UserConsent
from api.permissions import UserConsentPermission
from api.serializers import UserConsentSerializer


class UserConsentViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserConsentSerializer
    permission_classes = [UserConsentPermission, ]
    queryset = UserConsent.objects.all()
