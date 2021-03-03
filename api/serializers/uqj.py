from rest_framework import serializers

from course.models.models import UserQuestionJunction


class UQJSerializer(serializers.ModelSerializer):
    format = serializers.SerializerMethodField('get_format')
    category = serializers.SerializerMethodField('get_category')
    subcategory = serializers.SerializerMethodField('get_subcategory')

    def get_format(self, uqj):
        return uqj.question.type_name

    def get_category(self, uqj):
        return uqj.question.category.parent if uqj.question.category.parent else None

    def get_subcategory(self, uqj):
        return uqj.question.category.name

    class Meta:
        model = UserQuestionJunction
        fields = ['id',
                  'random_seed',
                  'last_viewed',
                  'opened_tutorial',
                  'tokens_received',
                  'is_solved',
                  'is_partially_solved',
                  'question',
                  'num_attempts',
                  'format',
                  'category',
                  'subcategory',
                  'status',
                  'formatted_current_tokens_received']
        depth = 1
