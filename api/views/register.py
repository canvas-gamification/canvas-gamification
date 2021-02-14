from rest_framework import mixins, viewsets

from accounts.models import MyUser
from api.serializers.register import UserRegistrationSerializer


class UserRegistrationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserRegistrationSerializer
    queryset = MyUser.objects.all()

    def create(self, request, *args, **kwargs):
        user = super().create(request, *args, **kwargs)
        # send_activation_email(request, user)
        return user
