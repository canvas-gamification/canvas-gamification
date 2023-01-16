from datetime import timedelta

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import api.error_messages as ERROR_MESSAGES
from api.serializers.goal import GoalSerializer, GoalItemSerializer
from canvas.models.goal import Goal, GoalItem
from canvas.services.goal import get_goal_stats
from course.models.models import QuestionCategory
from course.services.question import get_unsolved_practice_questions_count_by_category
from general.services.action import create_goal_action, create_goal_item_action


class GoalViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = GoalSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["course_reg__course_id"]
    queryset = Goal.objects.all()

    def get_queryset(self):
        return Goal.objects.filter(course_reg__user=self.request.user)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        goal = serializer.data
        create_goal_action(goal, self.request.user)

    @action(detail=True, methods=["post"], url_path="claim")
    def claim(self, request, pk):
        goal = get_object_or_404(self.get_queryset(), pk=pk)
        if goal.progress < goal.number_of_questions:
            raise ValidationError(ERROR_MESSAGES.GOAL.NOT_COMPLETED)
        goal.claimed = True
        goal.save()
        return Response()

    @action(detail=True, methods=["get"], url_path="stats")
    def stats(self, request, pk):
        goal = get_object_or_404(self.get_queryset(), pk=pk)
        return Response(get_goal_stats(goal))

    @action(detail=False, methods=["get"], url_path="limits")
    def limits(self, request):
        result = get_unsolved_practice_questions_count_by_category(request.user.id)
        return Response(result)

    @action(detail=False, methods=["get"], url_path="suggestions")
    def suggestions(self, request):
        category = QuestionCategory.objects.first()
        category2 = QuestionCategory.objects.last()

        data = [
            {
                "end_date": timezone.now() + timedelta(7),
                "goal_items": [
                    {
                        "category": category.id,
                        "category_name": category.full_name,
                        "difficulty": "EASY",
                        "number_of_questions": 2,
                    },
                    {
                        "category": category.id,
                        "category_name": category.full_name,
                        "difficulty": "MEDIUM",
                        "number_of_questions": 3,
                    },
                ],
            },
            {
                "end_date": timezone.now() + timedelta(7),
                "goal_items": [
                    {
                        "category": category2.id,
                        "category_name": category2.full_name,
                        "difficulty": "EASY",
                        "number_of_questions": 5,
                    },
                    {
                        "category": category2.id,
                        "category_name": category2.full_name,
                        "difficulty": "MEDIUM",
                        "number_of_questions": 5,
                    },
                    {
                        "category": category2.id,
                        "category_name": category2.full_name,
                        "difficulty": "HARD",
                        "number_of_questions": 5,
                    },
                ],
            },
        ]
        return Response(data)


class GoalItemViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = GoalItemSerializer

    def perform_create(self, serializer):
        super().perform_create(serializer)
        goal_item = serializer.data
        create_goal_item_action(goal_item, self.request.user)

    def get_queryset(self):
        return GoalItem.objects.filter(goal__course_reg__user=self.request.user)
