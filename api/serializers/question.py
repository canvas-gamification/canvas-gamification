from rest_framework import serializers

from api.serializers import EventSerializer
from course.models.models import Question


class QuestionSerializer(serializers.ModelSerializer):
    event = EventSerializer()
    status = serializers.SerializerMethodField('get_uqj_status')

    class Meta:
        model = Question
        fields = ['id', 'title', 'max_submission_allowed', 'time_created', 'time_modified', 'author', 'category',
                  'difficulty', 'is_verified', 'token_value', 'success_rate', 'type_name', 'event', 'is_sample',
                  'category_name', 'parent_category_name', 'course_name', 'event_name', 'author_name', 'status', ]

    def get_uqj_status(self, obj):
        request = self.context.get('request', None)
        return request.user.question_junctions.filter(question__pk=obj.id).first().status
