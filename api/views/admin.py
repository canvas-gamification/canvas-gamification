from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.permissions import TeacherAccessPermission
from api.serializers import QuestionCategorySerializer
from course.models.models import MultipleChoiceQuestion, JavaQuestion, QuestionCategory
from course.models.parsons_question import ParsonsQuestion


class AdminViewSet(viewsets.ViewSet):
    permission_classes = [TeacherAccessPermission, ]

    def list(self, request):
        return Response([])

    @action(detail=False, methods=['get'], url_path='question-count')
    def question_count(self, request):
        question_classes = [MultipleChoiceQuestion, JavaQuestion, ParsonsQuestion]
        return Response([{
            "name": QuestionClass._meta.verbose_name.title(),
            "count": QuestionClass.objects.count(),
        } for QuestionClass in question_classes])

    def get_nested_categories(self, parent_category=None):
        if parent_category is None:
            parent_categories = QuestionCategory.objects.filter(parent__isnull=True).all()
            return [self.get_nested_categories(category) for category in parent_categories]

        return {
            "category": QuestionCategorySerializer(parent_category).data,
            "children": [self.get_nested_categories(category) for category in parent_category.sub_categories.all()],
        }

    @action(detail=False, methods=['get'], url_path='category-stats')
    def category_stats(self, request):
        return Response(self.get_nested_categories())
