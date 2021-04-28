from rest_framework import serializers

from course.models.models import QuestionCategory


class QuestionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionCategory
        fields = ['pk', 'name', 'description', 'parent', 'question_count', 'average_success', 'next_category_ids',
                  'full_name']
