from rest_framework import serializers

from api.serializers import QuestionSerializer
from course.models.models import UserQuestionJunction, Question


class UQJSerializer(serializers.ModelSerializer):
    variables = serializers.SerializerMethodField("get_variables")
    variables_errors = serializers.SerializerMethodField("get_variables_errors")
    rendered_text = serializers.SerializerMethodField("get_rendered_text")
    rendered_choices = serializers.SerializerMethodField("get_rendered_choices")
    rendered_lines = serializers.SerializerMethodField("get_lines")
    input_files = serializers.SerializerMethodField("get_input_files")
    report = serializers.SerializerMethodField("get_report")
    question = QuestionSerializer(read_only=True)
    question_id = serializers.PrimaryKeyRelatedField(source="question", queryset=Question.objects.all())
    # Grade-revealing fields are masked while an exam is open (see ``_grades_hidden``).
    tokens_received = serializers.SerializerMethodField("get_tokens_received")
    is_solved = serializers.SerializerMethodField("get_is_solved")
    is_partially_solved = serializers.SerializerMethodField("get_is_partially_solved")
    status = serializers.SerializerMethodField("get_status")

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

    def _grades_hidden(self, uqj):
        """
        While an exam is open a student must not learn whether their answers are
        right. ``formatted_current_tokens_received`` already hides this; the raw
        fields have to follow the same rule. Staff who can edit the question see
        everything.
        """
        if not uqj.question.is_exam_and_open:
            return False
        request = self.context.get("request", None)
        user = getattr(request, "user", None) if request is not None else None
        if user is not None and user.is_authenticated and uqj.question.has_edit_permission(user):
            return False
        return True

    def get_tokens_received(self, uqj):
        return None if self._grades_hidden(uqj) else uqj.tokens_received

    def get_is_solved(self, uqj):
        return None if self._grades_hidden(uqj) else uqj.is_solved

    def get_is_partially_solved(self, uqj):
        return None if self._grades_hidden(uqj) else uqj.is_partially_solved

    def get_status(self, uqj):
        if self._grades_hidden(uqj):
            return "Submitted" if uqj.num_attempts() > 0 else "Not Submitted"
        return uqj.status

    class Meta:
        model = UserQuestionJunction
        fields = [
            "id",
            "last_viewed",
            "opened_tutorial",
            "tokens_received",
            "is_solved",
            "is_partially_solved",
            "question",
            "question_id",
            "num_attempts",
            "status",
            "formatted_current_tokens_received",
            "is_allowed_to_submit",
            "variables",
            "variables_errors",
            "rendered_text",
            "rendered_choices",
            "rendered_lines",
            "input_files",
            "is_checkbox",
            "report",
            "is_favorite",
        ]
