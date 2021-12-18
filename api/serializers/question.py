from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from api.serializers import EventSerializer, QuestionCategorySerializer
from course.models.models import Question


class QuestionSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField('get_uqj_status')
    is_author = serializers.SerializerMethodField('get_is_author')
    event_obj = SerializerMethodField('get_event_obj')
    category_obj = SerializerMethodField('get_category_obj')

    class Meta:
        model = Question
        fields = ['id', 'title', 'text', 'max_submission_allowed', 'time_created', 'time_modified', 'author',
                  'author_name', 'difficulty', 'is_verified', 'token_value', 'success_rate', 'type_name', 'event',
                  'event_obj', 'category', 'category_obj', 'parent_category_name', 'course', 'status', 'is_sample',
                  'is_open', 'is_exam', 'is_exam_and_open', 'is_author', 'is_practice']

    def get_uqj_status(self, obj):
        request = self.context.get('request', None)
        if request is None:
            return ''
        return request.user.question_junctions.get(question__pk=obj.id).status

    def get_is_author(self, obj):
        request = self.context.get('request', None)
        if request is None:
            return False
        return request.user == obj.author

    def get_event_obj(self, question):
        return EventSerializer(question.event).data

    def get_category_obj(self, question):
        return QuestionCategorySerializer(question.category).data
