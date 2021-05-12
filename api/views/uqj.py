from django_filters.rest_framework import DjangoFilterBackend
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
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, ]
    ordering_fields = ['last_viewed', ]
    filterset_fields = ['question', 'question__event', ]

    def get_queryset(self):
        user = self.request.user
        uqj = user.question_junctions.filter(user=user)
        accessible_uqj = []
        for temp in uqj:
            if temp.question.has_view_permission(user):
                accessible_uqj.append(temp)
            # TODO remove uqj from queryset if user does not have view permission.
            # else:
            # uqj = uqj.exclude(temp)
        print(accessible_uqj)
        return uqj
