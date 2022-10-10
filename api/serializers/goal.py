from rest_framework import serializers

from canvas.models.goal import Goal


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ["course_reg", "category", "difficulty", "end_date", "progress", "is_finished", "number_of_questions"]
