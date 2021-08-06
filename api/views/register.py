from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

import api.error_messages as ERROR_MESSAGES
from accounts.models import MyUser
from accounts.utils.email_functions import send_activation_email, activate_user
from api.serializers import UserRegistrationSerializer


class UserRegistrationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserRegistrationSerializer
    queryset = MyUser.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        send_activation_email(request, user)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['post'])
    def activate(self, request):
        uuid = request.data.get("uuid", None)
        token = request.data.get("token", None)
        user = activate_user(uuid, token)
        if not user:
            raise ValidationError(ERROR_MESSAGES.ACTIVATION.INVALID)
        return Response(status=status.HTTP_200_OK)
