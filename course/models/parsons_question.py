from course.models import VariableQuestion, Submission
from course.fields import JSONField


class ParsonsQuestion(VariableQuestion):
    lines = JSONField(default='[]')


class ParsonsSubmission(Submission):
    pass
