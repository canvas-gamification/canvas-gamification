from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from api.permissions import TeacherAccessPermission
from api.serializers import TokenValueSerializer
from course.models.models import DIFFICULTY_CHOICES
from course.models.models import QuestionCategory
from course.utils.utils import get_token_values, get_token_value_object


class TokenValueViewSet(viewsets.GenericViewSet,
                        mixins.UpdateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin):
    serializer_class = TokenValueSerializer
    permission_classes = [TeacherAccessPermission, ]

    def get_queryset(self):
        return get_token_values()

    def get_nested_token_values(self, parent_category=None):
        if parent_category is None:
            parent_categories = QuestionCategory.objects.filter(parent__isnull=True).all()
            return [self.get_nested_token_values(category) for category in parent_categories]

        return {
            "token_values": [
                self.get_serializer_class()(get_token_value_object(parent_category, difficulty)).data
                for difficulty, x in DIFFICULTY_CHOICES],
            "children": [self.get_nested_token_values(category) for category in parent_category.sub_categories.all()],
            "category_name": parent_category.name,
        }

    @action(detail=False, methods=['get'])
    def nested(self, request):
        return Response(self.get_nested_token_values())

    @action(detail=False, methods=['patch'], url_path='update-bulk')
    def update_bulk(self, request: Request):
        qs = self.get_queryset()
        data = request.data.get("data", [])
        for token_value in data:
            qs.filter(pk=token_value['id']).update(value=token_value['value'])
        return Response()
