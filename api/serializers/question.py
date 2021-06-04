from rest_framework import serializers

from api.serializers import EventSerializer
from course.models.models import Question


class QuestionSerializer(serializers.ModelSerializer):
    event = EventSerializer()
    status = serializers.SerializerMethodField('get_uqj_status')
    is_author = serializers.SerializerMethodField('get_is_author')

    class Meta:
        model = Question
        fields = ['id', 'title', 'text', 'max_submission_allowed', 'time_created', 'time_modified', 'author',
                  'category', 'difficulty', 'is_verified', 'token_value', 'success_rate', 'type_name', 'event',
                  'is_sample', 'category_name', 'parent_category_name', 'course_name', 'event_name', 'author_name',
                  'is_open', 'is_exam', 'is_exam_and_open', 'status', 'full_category_name', 'is_author']

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
