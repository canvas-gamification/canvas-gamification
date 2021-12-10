from rest_framework import serializers

from api.serializers import QuestionSerializer
from course.models.models import UserQuestionJunction, Question


class UQJSerializer(serializers.ModelSerializer):
    variables = serializers.SerializerMethodField('get_variables')
    variables_errors = serializers.SerializerMethodField('get_variables_errors')
    rendered_text = serializers.SerializerMethodField('get_rendered_text')
    rendered_choices = serializers.SerializerMethodField('get_rendered_choices')
    rendered_lines = serializers.SerializerMethodField('get_lines')
    input_files = serializers.SerializerMethodField('get_input_files')
    report = serializers.SerializerMethodField('get_report')
    question = QuestionSerializer(read_only=True)
    question_id = serializers.PrimaryKeyRelatedField(source='question', queryset=Question.objects.all())

    def get_variables(self, uqj):
        return uqj.get_variables()

    def get_variables_errors(self, uqj):
        return uqj.get_variables_errors()

    def get_rendered_text(self, uqj):
        return uqj.get_rendered_text()

    def get_rendered_choices(self, uqj):
        return uqj.get_rendered_choices()

    def get_lines(self, uqj):
        return uqj.get_lines()

    def get_input_files(self, uqj):
        return uqj.get_input_files()

    def get_report(self, uqj):
        from general.models.question_report import QuestionReport
        from api.serializers import QuestionReportSerializer
        queryset = QuestionReport.objects.all().filter(user=uqj.user_id, question=uqj.question_id)
        if queryset:
            return QuestionReportSerializer(queryset[0]).data
        else:
            return {}

    class Meta:
        model = UserQuestionJunction
        fields = ['id', 'last_viewed', 'opened_tutorial', 'tokens_received', 'is_solved', 'is_partially_solved',
                  'question', 'question_id', 'num_attempts', 'status', 'formatted_current_tokens_received',
                  'is_allowed_to_submit', 'variables', 'variables_errors', 'rendered_text', 'rendered_choices',
                  'rendered_lines', 'status_class', 'input_files', 'is_checkbox', 'report', 'is_favorite']
