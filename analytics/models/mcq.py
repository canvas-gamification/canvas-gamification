from django.db import models
from analytics.models.models import SubmissionAnalytics, QuestionAnalytics


class MCQSubmissionAnalytics(SubmissionAnalytics):
    answer = models.CharField(max_length=5, default="n/a")


class MCQQuestionAnalytics(QuestionAnalytics):
    pass
