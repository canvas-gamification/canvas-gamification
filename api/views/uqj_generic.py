from rest_framework import viewsets
from course.models.models import UserQuestionJunction
from api.serializers import UQJSerializer

from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response


class UQJGenericViewSet(viewsets.GenericViewSet):
    """
    Query Parameters
    + Standard ordering is applied on the field 'last_viewed'
    """
    serializer_class = UQJSerializer

    @action(detail=False, methods=['post'], url_path='switch-favorite')
    def switch_favorite(self, request, pk=None):
        """
        Updates "is_favorite" for UserQuestionJunction
        """
        status = request.data.get('status')
        junction_id = request.data.get('id')
        uqj = get_object_or_404(UserQuestionJunction, id=junction_id)
        uqj.is_favorite = status
        uqj.save()
        return Response(request.data)
