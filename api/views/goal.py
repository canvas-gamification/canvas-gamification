from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers.goal import GoalSerializer, GoalItemSerializer
from canvas.models.goal import Goal, GoalItem
from course.models.models import QuestionCategory


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

    @action(detail=False, methods=["get"], url_path="suggestions")
    def suggestions(self, request):
        category = QuestionCategory.objects.first()

        goals = [Goal(course_reg_id=1, end_date=timezone.now()) for _ in range(2)]

        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)


class GoalItemViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = GoalItemSerializer

    def get_queryset(self):
        return GoalItem.objects.filter(goal__course_reg__user=self.request.user)
