from rest_framework import serializers

from canvas.models.goal import Goal, GoalItem
from canvas.models.models import CanvasCourse
from canvas.utils.utils import get_course_registration


class GoalItemInnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalItem
        fields = ["id", "category", "difficulty", "progress", "number_of_questions", "category_name"]


class GoalItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalItem
        fields = ["id", "goal", "category", "difficulty", "progress", "number_of_questions", "category_name"]


class GoalSerializer(serializers.ModelSerializer):
    goal_items = GoalItemInnerSerializer(many=True, read_only=True)
    course_id = serializers.CharField(max_length=200, write_only=True)

    def create(self, validated_data):
        user = self.context["request"].user
        course_id = validated_data.pop("course_id", None)
        course = CanvasCourse.objects.get(id=course_id)
        validated_data["course_reg"] = get_course_registration(user, course)

        return super().create(validated_data)

    class Meta:
        model = Goal
        fields = [
            "id",
            "course_id",
            "end_date",
            "start_date",
            "progress",
            "is_finished",
            "number_of_questions",
            "goal_items",
            "stats",
            "claimed",
        ]
        read_only_fields = [
            "start_date",
        ]
