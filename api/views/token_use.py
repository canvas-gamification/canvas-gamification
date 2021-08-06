from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.permissions import StudentsMustBeRegisteredPermission
import api.error_messages as ERROR_MESSAGES
from canvas.models import CanvasCourse
from canvas.utils.token_use import update_token_use, TokenUseException


class TokenUseViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['POST'], url_path="use/(?P<course_pk>[^/.]+)",
            permission_classes=[StudentsMustBeRegisteredPermission, ])
    def use_tokens(self, request, course_pk=None):

        if course_pk is None or not request.data:
            raise ValidationError(ERROR_MESSAGES.COURSE.REQUIRED)

        course = get_object_or_404(CanvasCourse, pk=course_pk)
        try:
            update_token_use(request.user, course, request.data)
            return Response(status=status.HTTP_200_OK)
        except TokenUseException:
            raise ValidationError(ERROR_MESSAGES.TOKEN_USE.INVALID)
