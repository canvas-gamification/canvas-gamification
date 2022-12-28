from rest_framework import filters, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from api.pagination import BasePagination
from api.serializers import ActionsSerializer


class ActionsViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
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
