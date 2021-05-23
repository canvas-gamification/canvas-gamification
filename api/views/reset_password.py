from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from accounts.models import MyUser
from accounts.utils.email_functions import send_reset_email, verify_reset
from api.serializers import ResetPasswordSerializer


class ResetPasswordViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ResetPasswordSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['post'], url_path='send-email')
    def send_email(self, request):
        email = request.data.get("email", None)
        user = get_object_or_404(MyUser, email=email)
        send_reset_email(request, user)
        return Response("Email Sent")

    @action(detail=False, methods=['post'], url_path='validate')
    def validate(self, request):
        uuid = request.data.get("uuid", None)
        token = request.data.get("token", None)
        user = verify_reset(uuid, token)
        if not user:
            raise ValidationError("invalid reset data")
        else:
            return Response("Validated Successfully")
