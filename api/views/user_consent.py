from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import UserConsent
from api.serializers import UserConsentSerializer


class UserConsentViewSet(viewsets.ModelViewSet):
    # TODO: Check Authentication!!! and dont let people delete/edit
    def get_queryset(self):
        return UserConsent.objects.filter(user=self.request.user.id)

    serializer_class = UserConsentSerializer
    permission_classes = [IsAuthenticated, ]

    def perform_create(self, serializer):
        request = serializer.context['request']
        serializer.save(user=request.user)
