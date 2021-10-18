from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from accounts.models import MyUser
from accounts.utils.email_functions import send_reset_email
from api.serializers import ResetPasswordSerializer
from general.services.action import reset_password_email_action, reset_password_action


class ResetPasswordViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ResetPasswordSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = force_text(urlsafe_base64_decode(serializer.validated_data['uid']))
        user = MyUser.objects.get(pk=uid)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        reset_password_action(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['post'], url_path='send-email')
    def send_email(self, request):
        email = request.data.get("email", None)
        user = get_object_or_404(MyUser, email=email)
        send_reset_email(request, user)
        reset_password_email_action(user)
        return Response(status=status.HTTP_200_OK)
