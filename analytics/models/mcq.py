from django.db import models
from polymorphic.utils import reset_polymorphic_ctype

from accounts.models import MyUser
from analytics.models.models import SubmissionAnalytics, QuestionAnalytics


class MCQSubmissionAnalytics(SubmissionAnalytics):
    answer = models.CharField(max_length=5, default="n/a")

    @staticmethod
    def create_submission_analytics(submission):
        user_obj = MyUser.objects.get(pk=submission.user.pk)
        try:
            sub_analytics = MCQSubmissionAnalytics.objects.get(submission=submission.pk)
        except MCQSubmissionAnalytics.DoesNotExist:
            MCQSubmissionAnalytics.objects.create(uqj=submission.uqj.pk, submission=submission.pk,
                                                  question=submission.question.pk,
                                                  event=submission.question.event.pk, user_id=submission.user,
                                                  first_name=user_obj.first_name, last_name=user_obj.last_name,
                                                  answer=submission.answer)
            reset_polymorphic_ctype(SubmissionAnalytics, MCQSubmissionAnalytics, ignore_existing=True)


class MCQQuestionAnalytics(QuestionAnalytics):
    pass
