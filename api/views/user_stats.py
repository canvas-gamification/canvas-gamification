from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from accounts.models import MyUser
from api.serializers import UserStatsSerializer
from api.services.stats import (
    get_category_stats,
    get_question_stats,
    get_challenge_stats,
    get_goal_stats,
    get_token_stats,
)
from course.models.models import DIFFICULTY_CHOICES, QuestionCategory
from course.utils.utils import calculate_average_success


class UserStatsViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return MyUser.objects.filter(id=self.request.user.id)

    serializer_class = UserStatsSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def list(self, request, *args, **kwargs):
        return Response(
            {
                "token_stats": get_token_stats(request.user),
                "challenge_stats": get_challenge_stats(request.user),
                "goal_stats": get_goal_stats(request.user),
                "question_stats": get_question_stats(request.user),
                "category_stats": get_category_stats(request.user),
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
