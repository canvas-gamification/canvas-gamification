from rest_framework import serializers

from canvas.models.goal import Goal, GoalItem


class GoalItemInnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalItem
        fields = ["category", "difficulty", "number_of_questions"]


class GoalItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalItem
        fields = ["goal", "category", "difficulty", "progress", "number_of_questions"]


class GoalSerializer(serializers.ModelSerializer):
    goal_items = GoalItemInnerSerializer(many=True, read_only=True)

    class Meta:
        model = Goal
        fields = [
            "course_reg",
            "end_date",
            "start_date",
            "progress",
            "is_finished",
            "number_of_questions",
            "goal_items",
        ]
        read_only_fields = [
            "start_date",
        ]
