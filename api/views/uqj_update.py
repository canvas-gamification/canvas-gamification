from rest_framework import viewsets
from course.models.models import UserQuestionJunction
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
    permission_classes = [IsAuthenticated, ]

    @action(detail=False, methods=['post'], url_path='update-favorite')
    def update_is_favorite(self, request, pk=None):
        """
        Updates "is_favorite" for UserQuestionJunction
        """
        status = request.data.get('status')
        junction_id = request.data.get('id')
        uqj = get_object_or_404(UserQuestionJunction, id=junction_id)
        uqj.is_favorite = status
        uqj.save()
        return Response(request.data)
