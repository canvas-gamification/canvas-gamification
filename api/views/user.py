from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, filters

from accounts.models import MyUser
from api.permissions import TeacherAccessPermission
from api.renderers import CSVRenderer
from api.serializers.user import UserSerializer


class ExportUserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = MyUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [TeacherAccessPermission]
    renderer_classes = [CSVRenderer]

    filter_backends = [filters.OrderingFilter, filters.SearchFilter, DjangoFilterBackend]
    ordering_fields = [
        "email",
        "date_joined",
    ]
    filterset_fields = {
        "first_name": ["exact"],
        "last_name": ["exact"],
        "date_joined": ["range", "lt", "gt"],
        "email": ["exact"],
        "role": ["exact"],
    }
    search_fields = ["first_name", "last_name", "email"]

    @property
    def default_response_headers(self):
        headers = super().default_response_headers
        headers["Content-Disposition"] = 'attachment; filename="consents.csv"'
        return headers
