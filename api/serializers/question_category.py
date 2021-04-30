from rest_framework import serializers

from course.models.models import QuestionCategory


class QuestionCategorySerializer(serializers.ModelSerializer):
    average_success_per_difficulty = serializers.JSONField(read_only=True)

    class Meta:
        model = QuestionCategory
        fields = ['pk', 'name', 'description', 'parent', 'question_count', 'average_success', 'next_category_ids',
                  'full_name', 'average_success_per_difficulty']
