from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, filters
from rest_framework.permissions import IsAuthenticated

from api.pagination import BasePagination
from api.permissions import TeacherAccessPermission
from api.renderers import CSVRenderer
from api.serializers.page_view import PageViewSerializer

from general.models.page_view import PageView


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


class ExportPageViewViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PageViewSerializer
    permission_classes = [TeacherAccessPermission]
    renderer_classes = [CSVRenderer]

    filter_backends = [filters.OrderingFilter, filters.SearchFilter, DjangoFilterBackend]
    ordering_fields = [
        "time_created",
    ]
    filterset_fields = {
        "time_created": ["range", "lt", "gt"],
        "user": ["exact"],
        "user__role": ["exact"],
    }
    search_fields = [
        "url",
    ]

    queryset = PageView.objects.all()

    @property
    def default_response_headers(self):
        headers = super().default_response_headers
        headers["Content-Disposition"] = 'attachment; filename="page_views.csv"'
        return headers
