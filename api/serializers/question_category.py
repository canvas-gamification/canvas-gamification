from rest_framework import serializers

from course.models.models import QuestionCategory


class QuestionCategorySerializer(serializers.ModelSerializer):
    numQuestions = serializers.SerializerMethodField('count_questions')
    avgSuccess = serializers.SerializerMethodField('get_avg_success')
    nextCategories = serializers.SerializerMethodField('next_categories_ids')

    def count_questions(self, category):
        return category.question_count

    def get_avg_success(self, category):
        return category.average_success

    def next_categories_ids(self, category):
        return category.next_category_ids

    class Meta:
        model = QuestionCategory
        fields = ['pk', 'name', 'description', 'parent', 'numQuestions', 'avgSuccess', 'nextCategories']
