from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField
from api.serializers import UQJSerializer

from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class UpdateUQJViewSet(viewsets.GenericViewSet):
    """
    Query Parameters
    + Standard ordering is applied on the field 'last_viewed'
    """

    serializer_class = UQJSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    @action(detail=False, methods=["post"], url_path="update-favorite")
    def update_is_favorite(self, request, pk=None):
        """
        Updates "is_favorite" for one of the caller's own UserQuestionJunctions
        """
        try:
            status = BooleanField().to_internal_value(request.data.get("status"))
        except ValidationError:
            raise ValidationError({"status": "Must be a boolean."})
        junction_id = request.data.get("id")
        uqj = get_object_or_404(request.user.question_junctions, id=junction_id)
        uqj.is_favorite = status
        uqj.save()
        return Response(request.data)
