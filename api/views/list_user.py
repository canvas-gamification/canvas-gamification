from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from accounts.models import MyUser
from canvas.models import CanvasCourseRegistration
from api.serializers import UsersCountSerializers

class UsersCountViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['role']

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = 0
        user.save()
        return Response(self.get_serializer(user).data)

    def get_queryset(self):
        return MyUser.objects

    serializer_class = UsersCountSerializers

