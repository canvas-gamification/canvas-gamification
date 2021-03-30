from rest_framework import serializers
from course.models.models import UserQuestionJunction


class UQJSerializer(serializers.ModelSerializer):
    variables = serializers.SerializerMethodField('get_variables')
    variables_errors = serializers.SerializerMethodField('get_variables_errors')
    rendered_text = serializers.SerializerMethodField('get_rendered_text')
    rendered_choices = serializers.SerializerMethodField('get_rendered_choices')
    rendered_lines = serializers.SerializerMethodField('get_lines')
    input_files = serializers.SerializerMethodField('get_input_files')

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

    class Meta:
        model = UserQuestionJunction
        fields = ['id', 'last_viewed', 'opened_tutorial', 'tokens_received', 'is_solved', 'is_partially_solved',
                  'question', 'num_attempts', 'status', 'formatted_current_tokens_received', 'is_allowed_to_submit',
                  'variables', 'variables_errors', 'rendered_text', 'rendered_choices', 'rendered_lines',
                  'status_class', 'input_files', 'question_title', 'question_type']
