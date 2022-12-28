from rest_framework import viewsets, mixins, filters
from rest_framework.permissions import IsAuthenticated

from api.pagination import BasePagination
from api.serializers.page_view import PageViewSerializer


class PageViewViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PageViewSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = BasePagination

    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
        "time_created",
    ]

    def perform_create(self, serializer):
        request = serializer.context["request"]
        serializer.save(user=request.user)

    def get_queryset(self):
        user = self.request.user
        return user.page_views.all()
