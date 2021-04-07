from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from canvas.models import CanvasCourse
from canvas.utils.token_use import update_token_use, TokenUseException


class TokenUseViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['POST'], url_path="use/(?P<course_pk>[^/.]+)",
            permission_classes=[IsAuthenticated, ])
    def use_tokens(self, request, course_pk=None):

        if course_pk is None or not request.data:
            raise ValidationError()

        course = get_object_or_404(CanvasCourse, pk=course_pk)
        try:
            update_token_use(request.user, course, request.data)
            return Response({"success": True})
        except TokenUseException:
            raise ValidationError()
