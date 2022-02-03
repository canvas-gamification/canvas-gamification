from accounts.models import MyUser
from analytics.models import JavaSubmissionAnalytics, ParsonsSubmissionAnalytics, MCQSubmissionAnalytics
from analytics.models.models import SubmissionAnalytics
from analytics.utils.init_analytics import SubmissionAnalyticsObj
from api.serializers.submission_analytics import JavaSubmissionAnalyticsSerializer, \
    ParsonsSubmissionAnalyticsSerializer, MCQSubmissionAnalyticsSerializer, SubmissionAnalyticsSerializer
from course.models.java import JavaSubmission
from course.models.models import Submission
from course.models.multiple_choice import MultipleChoiceSubmission
from course.models.parsons import ParsonsSubmission
from general.models.action import Action, ActionVerb


def get_submission_analytics(submission):
    try:
        analytics = SubmissionAnalytics.objects.get(submission=submission)
    except SubmissionAnalytics.DoesNotExist:
        return create_submission_analytics(submission)
    else:
        return SubmissionAnalyticsSerializer(analytics).data


def get_all_submission_analytics():
    submissions = Submission.objects.all()
    submission_num = Submission.objects.all().count()
    submission_analytics_num = SubmissionAnalytics.objects.all().count()
    if submission_num == submission_analytics_num:
        return SubmissionAnalyticsSerializer(SubmissionAnalytics.objects.all(), many=True).data
    else:
        for submission in submissions:
            create_submission_analytics(submission)
        return SubmissionAnalyticsSerializer(SubmissionAnalytics.objects.all(), many=True).data


def create_submission_analytics(submission):
    curr_uqj_submissions = Submission.objects.filter(uqj=submission.uqj.id)
    num_attempts = curr_uqj_submissions.count()
    user_obj = MyUser.objects.get(pk=submission.user.pk)
    time_spent = 0
    try:
        question_last_access_time = Action.objects \
            .filter(actor=user_obj, object_id=submission.question.id, verb=ActionVerb.OPENED) \
            .order_by('-time_created').first()
    except Action.DoesNotExist:
        pass
    else:
        if question_last_access_time:
            question_last_access_time = question_last_access_time.time_created
            submission_time = Action.objects \
                .filter(actor=user_obj, object_id=submission.id, verb=ActionVerb.SUBMITTED) \
                .order_by('-time_created').first().time_created
            time_diff = submission_time - question_last_access_time
            time_spent = time_diff.total_seconds()

    is_correct = False
    for item in curr_uqj_submissions:
        if item.is_correct is True:
            is_correct = True
            break

    if isinstance(submission, JavaSubmission):
        ans = submission.answer_files
        sub_analytics_dict = SubmissionAnalyticsObj(ans)

        submission_analytics_obj = JavaSubmissionAnalytics.objects.create(uqj=submission.uqj, submission=submission,
                                                                          question=submission.question,
                                                                          event=submission.question.event,
                                                                          user_id=submission.user,
                                                                          first_name=user_obj.first_name,
                                                                          last_name=user_obj.last_name,
                                                                          ans_file=ans, time_spent=time_spent,
                                                                          num_attempts=num_attempts,
                                                                          is_correct=is_correct,
                                                                          lines=sub_analytics_dict.lines,
                                                                          blank_lines=sub_analytics_dict.blank_lines,
                                                                          comment_lines=sub_analytics_dict.comment_lines,
                                                                          import_lines=sub_analytics_dict.imported_lines,
                                                                          cyclomatic_complexity=sub_analytics_dict.cc,
                                                                          method=sub_analytics_dict.method,
                                                                          operator=sub_analytics_dict.operator,
                                                                          operand=sub_analytics_dict.operand,
                                                                          unique_operator=sub_analytics_dict.unique_operator,
                                                                          unique_operand=sub_analytics_dict.unique_operand,
                                                                          vocab=sub_analytics_dict.vocab,
                                                                          size=sub_analytics_dict.size,
                                                                          vol=sub_analytics_dict.vol,
                                                                          difficulty=sub_analytics_dict.difficulty,
                                                                          effort=sub_analytics_dict.effort,
                                                                          error=sub_analytics_dict.error,
                                                                          test_time=sub_analytics_dict.test_time)
        return JavaSubmissionAnalyticsSerializer(submission_analytics_obj).data
    if isinstance(submission, ParsonsSubmission):
        ans = submission.answer_files
        sub_analytics_dict = SubmissionAnalyticsObj(ans)
        submission_analytics_obj = ParsonsSubmissionAnalytics.objects.create(uqj=submission.uqj, submission=submission,
                                                                             question=submission.question,
                                                                             event=submission.question.event,
                                                                             user_id=submission.user,
                                                                             first_name=user_obj.first_name,
                                                                             last_name=user_obj.last_name,
                                                                             ans_file=ans, time_spent=time_spent,
                                                                             num_attempts=num_attempts,
                                                                             is_correct=is_correct,
                                                                             lines=sub_analytics_dict.lines,
                                                                             blank_lines=sub_analytics_dict.blank_lines,
                                                                             comment_lines=sub_analytics_dict.comment_lines,
                                                                             import_lines=sub_analytics_dict.imported_lines,
                                                                             cyclomatic_complexity=sub_analytics_dict.cc,
                                                                             method=sub_analytics_dict.method,
                                                                             operator=sub_analytics_dict.operator,
                                                                             operand=sub_analytics_dict.operand,
                                                                             unique_operator=sub_analytics_dict.unique_operator,
                                                                             unique_operand=sub_analytics_dict.unique_operand,
                                                                             vocab=sub_analytics_dict.vocab,
                                                                             size=sub_analytics_dict.size,
                                                                             vol=sub_analytics_dict.vol,
                                                                             difficulty=sub_analytics_dict.difficulty,
                                                                             effort=sub_analytics_dict.effort,
                                                                             error=sub_analytics_dict.error,
                                                                             test_time=sub_analytics_dict.test_time)
        return ParsonsSubmissionAnalyticsSerializer(submission_analytics_obj).data
    if isinstance(submission, MultipleChoiceSubmission):
        submission_analytics_obj = MCQSubmissionAnalytics.objects.create(uqj=submission.uqj, submission=submission,
                                                                         question=submission.question,
                                                                         event=submission.question.event,
                                                                         user_id=submission.user,
                                                                         first_name=user_obj.first_name,
                                                                         last_name=user_obj.last_name,
                                                                         answer=submission.answer,
                                                                         time_spent=time_spent,
                                                                         num_attempts=num_attempts,
                                                                         is_correct=is_correct, )
        return MCQSubmissionAnalyticsSerializer(submission_analytics_obj).data
