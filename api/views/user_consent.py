from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import UserConsent
from api.permissions import UserConsentPermission
from api.serializers import UserConsentSerializer
from general.services.action import give_user_consent_action, remove_user_consent_action


class UserConsentViewSet(viewsets.ModelViewSet):
    queryset = UserConsent.objects.all()
    serializer_class = UserConsentSerializer
    permission_classes = [IsAuthenticated, UserConsentPermission]

    def perform_create(self, serializer):
        request = serializer.context['request']
        serializer.save(user=request.user)
        if request.data['consent']:
            user = request.user
            user.first_name = request.data['legal_first_name']
            user.last_name = request.data['legal_last_name']
            user.save()
            give_user_consent_action(request.user, request.data)
        else:
            remove_user_consent_action(request.user, request.data)
