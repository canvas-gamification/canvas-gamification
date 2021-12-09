from django.db import models

from accounts.models import MyUser
from analytics.models.models import SubmissionAnalytics, SubmissionAnalyticsObj
from course.fields import JSONField


class ParsonsSubmissionAnalytics(SubmissionAnalytics):
    lines = models.IntegerField(default=0)
    blank_lines = models.IntegerField(default=0)
    comment_lines = models.IntegerField(default=0)
    import_lines = models.IntegerField(default=0)
    cc = models.IntegerField(default=0)
    method = models.IntegerField(default=0)
    operator = models.IntegerField(default=0)
    operand = models.IntegerField(default=0)
    unique_operator = models.IntegerField(default=0)
    unique_operand = models.IntegerField(default=0)
    vocab = models.IntegerField(default=0)
    size = models.IntegerField(default=0)
    vol = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    difficulty = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    effort = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    error = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    test_time = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    ans_file = JSONField()

    @staticmethod
    def create_submission_analytics(submission):
        ans = submission.answer_files
        sub_analytics_dict = SubmissionAnalyticsObj(ans)
        user_obj = MyUser.objects.get(pk=submission.user.pk)
        try:
            sub_analytics = ParsonsSubmissionAnalytics.objects.get(submission=submission.pk)
        except ParsonsSubmissionAnalytics.DoesNotExist:
            ParsonsSubmissionAnalytics.objects.create(uqj=submission.uqj.pk, submission=submission.pk,
                                                      question=submission.question.pk,
                                                      event=submission.question.event.pk, user_id=submission.user,
                                                      first_name=user_obj.first_name, last_name=user_obj.last_name,
                                                      ans_file=ans, lines=sub_analytics_dict.lines,
                                                      blank_lines=sub_analytics_dict.blank_lines,
                                                      comment_lines=sub_analytics_dict.comment_lines,
                                                      import_lines=sub_analytics_dict.imported_lines,
                                                      cc=sub_analytics_dict.cc,
                                                      method=sub_analytics_dict.method,
                                                      operator=sub_analytics_dict.operator,
                                                      operand=sub_analytics_dict.operand,
                                                      unique_operator=sub_analytics_dict.unique_operator,
                                                      unique_operand=sub_analytics_dict.unique_operand,
                                                      vocab=sub_analytics_dict.vocab,
                                                      size=sub_analytics_dict.size, vol=sub_analytics_dict.vol,
                                                      difficulty=sub_analytics_dict.difficulty,
                                                      effort=sub_analytics_dict.effort,
                                                      error=sub_analytics_dict.error,
                                                      test_time=sub_analytics_dict.test_time)
