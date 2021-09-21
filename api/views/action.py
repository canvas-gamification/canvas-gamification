from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated

from api.pagination import BasePagination
from api.serializers import ActionsSerializer


class ActionsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Query Parameters
    + Standard ordering is applied
    """
    serializer_class = ActionsSerializer
    permission_classes = [IsAuthenticated, ]
    pagination_class = BasePagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['time_modified', 'time_created', 'id', 'object_type', 'status', 'verb']

    def get_queryset(self):
        user = self.request.user
        return user.actions.all()
