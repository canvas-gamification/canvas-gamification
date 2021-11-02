from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.permissions import TeacherAccessPermission
from api.serializers import QuestionCategorySerializer, CourseSerializer
from canvas.models import CanvasCourse
from course.models.java import JavaQuestion
from course.models.models import QuestionCategory, DIFFICULTY_CHOICES
from course.models.multiple_choice import MultipleChoiceQuestion
from course.models.parsons import ParsonsQuestion


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
                "count": QuestionClass.objects.count(),
                "count_per_difficulty": [{
                    'count': QuestionClass.objects.filter(difficulty=difficulty).count(),
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

    @action(detail=False, methods=['get'], url_path='courses')
    def courses(self, request):
        course_details = [CourseSerializer(course).data for course in CanvasCourse.objects.all()]
        return Response(course_details)
