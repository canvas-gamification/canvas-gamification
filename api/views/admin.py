from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.permissions import TeacherAccessPermission
from api.serializers import QuestionCategorySerializer
from course.models.models import MultipleChoiceQuestion, JavaQuestion, QuestionCategory, DIFFICULTY_CHOICES
from course.models.parsons_question import ParsonsQuestion
from course.utils.utils import get_question_count


class AdminViewSet(viewsets.ViewSet):
    permission_classes = [TeacherAccessPermission, ]

    def list(self, request):
        return Response([])

    @action(detail=False, methods=['get'], url_path='question-count')
    def question_count(self, request):
        question_classes = [MultipleChoiceQuestion, JavaQuestion, ParsonsQuestion]
        res = []
        for QuestionClass in question_classes:
            res.append({
                "name": QuestionClass._meta.verbose_name.title(),
                "count": get_question_count(QuestionClass),
                "count_per_difficulty": [{
                    'count': get_question_count(QuestionClass, difficulty),
                    'difficulty': difficulty_name,
                } for difficulty, difficulty_name in DIFFICULTY_CHOICES]
            })
        return Response(res)

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
