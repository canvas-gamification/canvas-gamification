from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated

from api.pagination import BasePagination
from api.serializers import UQJSerializer


class UQJViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Query Parameters
    + Standard ordering is applied on the field 'last_viewed'
    """
    serializer_class = UQJSerializer
    permission_classes = [IsAuthenticated, ]
    pagination_class = BasePagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['last_viewed', ]

    def get_queryset(self):
        user = self.request.user
        return user.question_junctions.all()
