from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.permissions import TeacherAccessPermission
from api.serializers import TokenValueSerializer
from course.utils.utils import get_token_values
from course.models.models import DIFFICULTY_CHOICES


class TokenValueViewSet(viewsets.GenericViewSet,
                        mixins.UpdateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin):
    serializer_class = TokenValueSerializer
    permission_classes = [TeacherAccessPermission, ]

    def get_queryset(self):
        return get_token_values()

    @action(detail=False, methods=['get'], url_path="get-difficulties")
    def get_registration_status(self, request, pk=None):
        difficulties = {x: y for x, y in DIFFICULTY_CHOICES}
        return Response({
            "difficulties": difficulties,
            "message": None,
        })
