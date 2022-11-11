from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from accounts.models import MyUser
from api.serializers import UserStatsSerializer
from course.models.models import DIFFICULTY_CHOICES, QuestionCategory
from course.utils.utils import calculate_average_success, calculate_solved_questions, success_rate


class UserStatsViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return MyUser.objects.filter(id=self.request.user.id)

    serializer_class = UserStatsSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def list(self, request, *args, **kwargs):
        category_stats = []

        for category in QuestionCategory.objects.all():
            for difficulty, _ in DIFFICULTY_CHOICES:
                solved, total = calculate_solved_questions(request.user.question_junctions, category, difficulty)
                category_stats.append(
                    {
                        "category": category.id,
                        "difficulty": difficulty,
                        "questions_attempt": total,
                        "questions_solved": solved,
                        "avgSuccess": success_rate(solved, total),
                    }
                )
            solved, total = calculate_solved_questions(request.user.question_junctions, category)
            category_stats.append(
                {
                    "category": category.id,
                    "difficulty": "ALL",
                    "questions_attempt": total,
                    "questions_solved": solved,
                    "avgSuccess": success_rate(solved, total),
                }
            )

        return Response(
            {
                "question_stats": category_stats,
            }
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="category/(?P<category_pk>[^/.]+)",
    )
    def difficulty(self, request, category_pk=None):
        user_stats = []
        category = QuestionCategory.objects.get(id=category_pk)

        for difficulty, _ in DIFFICULTY_CHOICES:
            user_stats.append(
                {
                    "difficulty": difficulty,
                    "avgSuccess": calculate_average_success(request.user.question_junctions, category, difficulty),
                }
            )
        user_stats.append(
            {
                "difficulty": "ALL",
                "avgSuccess": calculate_average_success(request.user.question_junctions, category),
            }
        )
        return Response(user_stats, status=status.HTTP_200_OK)
