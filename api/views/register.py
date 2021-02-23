from rest_framework import mixins, viewsets, status
from rest_framework.response import Response

from accounts.models import MyUser
from accounts.utils.email_functions import send_activation_email
from api.serializers.register import UserRegistrationSerializer


class UserRegistrationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserRegistrationSerializer
    queryset = MyUser.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        print(user)
        headers = self.get_success_headers(serializer.data)
        send_activation_email(request, user)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
