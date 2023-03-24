from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from api.pagination import BasePagination
from api.permissions import TeacherAccessPermission
from api.renderers import CSVRenderer
from api.serializers import ActionsSerializer
from general.models.action import Action


class ActionsViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """
    Query Parameters
    + Standard ordering is applied
    """

    serializer_class = ActionsSerializer
    permission_classes = [
        IsAuthenticated,
    ]
    pagination_class = BasePagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
        "time_modified",
        "time_created",
        "id",
        "object_type",
        "status",
        "verb",
    ]

    def perform_create(self, serializer):
        request = serializer.context["request"]
        serializer.save(actor=request.user)

    def get_queryset(self):
        user = self.request.user
        return user.actions.all()


class ExportActionViewSet(
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = ActionsSerializer
    permission_classes = [
        TeacherAccessPermission,
    ]
    renderer_classes = [CSVRenderer]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter, DjangoFilterBackend]
    ordering_fields = [
        "time_modified",
        "time_created",
        "id",
        "object_type",
        "status",
        "verb",
    ]
    filterset_fields = {
        "time_created": ["range", "lt", "gt"],
        "time_modified": ["range", "lt", "gt"],
        "actor": ["exact"],
        "token_change": ["exact", "lt", "gt"],
        "status": ["exact"],
        "verb": ["exact"],
        "object_type": ["exact"],
        "object_id": ["exact"],
    }
    search_fields = ["data", "description"]
    queryset = Action.objects.all()

    @property
    def default_response_headers(self):
        headers = super().default_response_headers
        headers["Content-Disposition"] = 'attachment; filename="actions.csv"'
        return headers
