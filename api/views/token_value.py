from rest_framework import viewsets, mixins

from api.permissions import TeacherAccessPermission
from api.serializers import TokenValueSerializer
from course.utils.utils import get_token_values


class TokenValueViewSet(viewsets.GenericViewSet,
                        mixins.UpdateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin):
    serializer_class = TokenValueSerializer
    permission_classes = [TeacherAccessPermission, ]

    def get_queryset(self):
        return get_token_values()
