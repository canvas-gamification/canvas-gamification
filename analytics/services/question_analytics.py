import json
from datetime import datetime
from django.utils.timezone import utc

from analytics.models import JavaSubmissionAnalytics, MCQSubmissionAnalytics, ParsonsSubmissionAnalytics
from analytics.models.java import JavaQuestionAnalytics
from analytics.models.mcq import MCQQuestionAnalytics
from analytics.models.models import QuestionAnalytics, SubmissionAnalytics
import statistics

from analytics.models.parsons import ParsonsQuestionAnalytics
from analytics.services.submission_analytics import get_all_submission_analytics
from api.serializers.question_analytics import QuestionAnalyticsSerializer, JavaQuestionAnalyticsSerializer, \
    MCQQuestionAnalyticsSerializer, ParsonsQuestionAnalyticsSerializer
from canvas.models import Event
from course.models.models import Question
from course.models.java import JavaQuestion
from course.models.parsons import ParsonsQuestion
from course.models.multiple_choice import MultipleChoiceQuestion
from django.db.models import Avg, Max


def get_question_analytics(question):
    # 1 if cache and question analytics exists return that
    # 2 calculate question analytics and save it in the database
    # 3 make sure to replace the old one

    # if the question analytics exists and cache is true but the cache is old
    # still calculate it

    # move this to a separate file
    try:
        if isinstance(question, JavaQuestion):
            analytics = JavaQuestionAnalytics.objects.get(question=question)
        if isinstance(question, ParsonsQuestion):
            analytics = ParsonsQuestionAnalytics.objects.get(question=question)
        if isinstance(question, MultipleChoiceQuestion):
            analytics = MCQQuestionAnalytics.objects.get(question=question)

    except QuestionAnalytics.DoesNotExist:
        return create_question_analytics(question)
    else:
        now = datetime.utcnow().replace(tzinfo=utc)
        time_diff = now - analytics.time_created
        time_diff = time_diff.total_seconds()
        # the analytics expires after one day
        if time_diff < 86400:
            if isinstance(analytics, JavaQuestionAnalytics):
                return JavaQuestionAnalyticsSerializer(analytics).data
            if isinstance(analytics, ParsonsQuestionAnalytics):
                return ParsonsQuestionAnalyticsSerializer(analytics).data
            if isinstance(analytics, MCQQuestionAnalytics):
                return MCQQuestionAnalyticsSerializer(analytics).data
        else:
            return create_question_analytics(question)


def get_all_question_analytics():
    distinct_events = SubmissionAnalytics.objects.values_list('event', flat=True).distinct()
    for event_id in distinct_events:
        event = Event.objects.get(id=event_id)
        course = event.course
        question_list = SubmissionAnalytics.objects \
            .filter(event=event).values_list('question', flat=True).distinct()
        for question_id in question_list:
            question = Question.objects.get(id=question_id)
            try:
                analytics = QuestionAnalytics.objects.get(question=question)
            except QuestionAnalytics.DoesNotExist:
                return create_question_analytics(question)
            else:
                now = datetime.utcnow().replace(tzinfo=utc)
                time_diff = now - analytics.time_created
                time_diff = time_diff.total_seconds()
                # the analytics expires after one day
                if time_diff > 86400:
                    create_question_analytics(question)
    return QuestionAnalyticsSerializer(QuestionAnalytics.objects.all(), many=True).data


def create_question_analytics(question):
    get_all_submission_analytics()
    event = question.event
    course = question.course
    analytics_by_question = SubmissionAnalytics.objects.filter(question=question)
    num_respondents = analytics_by_question.values_list('user_id', flat=True).distinct().count()
    if num_respondents == 0:
        return 'No Submission Analytics are found.'
    total_attempts = 0
    attempts = []
    total_grade = 0
    grade = []
    time_spent = []
    distinct_user = []
    for item in analytics_by_question:

        total_grade += item.submission.grade
        grade.append(item.submission.grade)
        time_spent.append(item.time_spent)

    distinct_user = analytics_by_question.values('user_id').distinct()
    for user in distinct_user:
        total_attempts += analytics_by_question.filter(user_id=user['user_id']).aggregate(Max('num_attempts'))['num_attempts__max']
        attempts.append(analytics_by_question.filter(user_id=user['user_id']).aggregate(Max('num_attempts'))['num_attempts__max'])

    avg_attempt = total_attempts / num_respondents
    attempt_std_dev = statistics.stdev(attempts) if len(attempts) > 1 else 0
    avg_grade = total_grade / num_respondents
    grade_std_dev = statistics.stdev(grade) if len(grade) > 1 else 0

    time_spent = [i for i in time_spent if i > 0]
    median_time_spent = statistics.median(time_spent) if len(time_spent) != 0 else 0

    if isinstance(analytics_by_question.first(), JavaSubmissionAnalytics):
        lines = analytics_by_question.aggregate(Avg('javasubmissionanalytics__lines'))
        blank_lines = analytics_by_question.aggregate(Avg('javasubmissionanalytics__blank_lines'))
        comment_lines = analytics_by_question.aggregate(Avg('javasubmissionanalytics__comment_lines'))
        import_lines = analytics_by_question.aggregate(Avg('javasubmissionanalytics__import_lines'))
        cc = analytics_by_question.aggregate(Avg('javasubmissionanalytics__cc'))
        method = analytics_by_question.aggregate(Avg('javasubmissionanalytics__method'))
        operator = analytics_by_question.aggregate(Avg('javasubmissionanalytics__operator'))
        operand = analytics_by_question.aggregate(Avg('javasubmissionanalytics__operand'))
        unique_operator = analytics_by_question.aggregate(Avg('javasubmissionanalytics__unique_operator'))
        unique_operand = analytics_by_question.aggregate(Avg('javasubmissionanalytics__unique_operand'))
        vocab = analytics_by_question.aggregate(Avg('javasubmissionanalytics__vocab'))
        size = analytics_by_question.aggregate(Avg('javasubmissionanalytics__size'))
        vol = analytics_by_question.aggregate(Avg('javasubmissionanalytics__vol'))
        difficulty = analytics_by_question.aggregate(Avg('javasubmissionanalytics__difficulty'))
        effort = analytics_by_question.aggregate(Avg('javasubmissionanalytics__effort'))
        error = analytics_by_question.aggregate(Avg('javasubmissionanalytics__error'))
        test_time = analytics_by_question.aggregate(Avg('javasubmissionanalytics__test_time'))

        try:
            question_analytics = JavaQuestionAnalytics.objects.get(question=question)
        except JavaQuestionAnalytics.DoesNotExist:
            question_analytics = JavaQuestionAnalytics.objects.create(
                question=question,
                event=event,
                course=course,
                most_frequent_wrong_ans='',
                avg_grade=avg_grade,
                grade_std_dev=grade_std_dev,
                num_respondents=num_respondents,
                avg_attempt=avg_attempt,
                attempt_std_dev=attempt_std_dev,
                median_time_spent=median_time_spent,
                lines=[elem for elem in lines.values()][0],
                blank_lines=[elem for elem in blank_lines.values()][0],
                comment_lines=[elem for elem in comment_lines.values()][0],
                import_lines=[elem for elem in import_lines.values()][0],
                cc=[elem for elem in cc.values()][0],
                method=[elem for elem in method.values()][0],
                operator=[elem for elem in operator.values()][0],
                operand=[elem for elem in operand.values()][0],
                unique_operator=[elem for elem in unique_operator.values()][0],
                unique_operand=[elem for elem in unique_operand.values()][0],
                vocab=[elem for elem in vocab.values()][0],
                size=[elem for elem in size.values()][0],
                vol=[elem for elem in vol.values()][0],
                difficulty=[elem for elem in difficulty.values()][0],
                effort=[elem for elem in effort.values()][0],
                error=[elem for elem in error.values()][0],
                test_time=[elem for elem in test_time.values()][0]

            )
        else:
            question_analytics.time_created = datetime.utcnow().replace(tzinfo=utc)
            question_analytics.most_frequent_wrong_ans = ''
            question_analytics.avg_grade = avg_grade
            question_analytics.grade_std_dev = grade_std_dev
            question_analytics.num_respondents = num_respondents
            question_analytics.avg_attempt = avg_attempt
            question_analytics.attempt_std_dev = attempt_std_dev
            question_analytics.median_time_spent = median_time_spent
            question_analytics.lines = [elem for elem in lines.values()][0]
            question_analytics.blank_lines = [elem for elem in blank_lines.values()][0]
            question_analytics.comment_lines = [elem for elem in comment_lines.values()][0]
            question_analytics.import_lines = [elem for elem in import_lines.values()][0]
            question_analytics.cc = [elem for elem in cc.values()][0]
            question_analytics.method = [elem for elem in method.values()][0]
            question_analytics.operator = [elem for elem in operator.values()][0]
            question_analytics.operand = [elem for elem in operand.values()][0]
            question_analytics.unique_operator = [elem for elem in unique_operator.values()][0]
            question_analytics.unique_operand = [elem for elem in unique_operand.values()][0]
            question_analytics.vocab = [elem for elem in vocab.values()][0]
            question_analytics.size = [elem for elem in size.values()][0]
            question_analytics.vol = [elem for elem in vol.values()][0]
            question_analytics.difficulty = [elem for elem in difficulty.values()][0]
            question_analytics.effort = [elem for elem in effort.values()][0]
            question_analytics.error = [elem for elem in error.values()][0]
            question_analytics.test_time = [elem for elem in test_time.values()][0]
            question_analytics.save()
        return JavaQuestionAnalyticsSerializer(question_analytics).data
    if isinstance(analytics_by_question.first(), ParsonsSubmissionAnalytics):
        lines = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__lines'))
        blank_lines = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__blank_lines'))
        comment_lines = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__comment_lines'))
        import_lines = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__import_lines'))
        cc = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__cc'))
        method = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__method'))
        operator = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__operator'))
        operand = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__operand'))
        unique_operator = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__unique_operator'))
        unique_operand = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__unique_operand'))
        vocab = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__vocab'))
        size = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__size'))
        vol = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__vol'))
        difficulty = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__difficulty'))
        effort = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__effort'))
        error = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__error'))
        test_time = analytics_by_question.aggregate(Avg('parsonssubmissionanalytics__test_time'))

        try:
            question_analytics = ParsonsQuestionAnalytics.objects.get(question=question)
        except ParsonsQuestionAnalytics.DoesNotExist:
            question_analytics = ParsonsQuestionAnalytics.objects.create(
                question=question,
                event=event,
                course=course,
                lines=[elem for elem in lines.values()][0],
                blank_lines=[elem for elem in blank_lines.values()][0],
                comment_lines=[elem for elem in comment_lines.values()][0],
                import_lines=[elem for elem in import_lines.values()][0],
                cc=[elem for elem in cc.values()][0],
                method=[elem for elem in method.values()][0],
                operator=[elem for elem in operator.values()][0],
                operand=[elem for elem in operand.values()][0],
                unique_operator=[elem for elem in unique_operator.values()][0],
                unique_operand=[elem for elem in unique_operand.values()][0],
                vocab=[elem for elem in vocab.values()][0],
                size=[elem for elem in size.values()][0],
                vol=[elem for elem in vol.values()][0],
                difficulty=[elem for elem in difficulty.values()][0],
                effort=[elem for elem in effort.values()][0],
                error=[elem for elem in error.values()][0],
                test_time=[elem for elem in test_time.values()][0],
                most_frequent_wrong_ans='',
                avg_grade=avg_grade,
                grade_std_dev=grade_std_dev,
                num_respondents=num_respondents,
                avg_attempt=avg_attempt,
                attempt_std_dev=attempt_std_dev,
                median_time_spent=median_time_spent,
            )
        else:
            question_analytics.time_created = datetime.utcnow().replace(tzinfo=utc)
            question_analytics.most_frequent_wrong_ans = ''
            question_analytics.avg_grade = avg_grade
            question_analytics.grade_std_dev = grade_std_dev
            question_analytics.num_respondents = num_respondents
            question_analytics.avg_attempt = avg_attempt
            question_analytics.attempt_std_dev = attempt_std_dev
            question_analytics.median_time_spent = median_time_spent
            question_analytics.lines = [elem for elem in lines.values()][0]
            question_analytics.blank_lines = [elem for elem in blank_lines.values()][0]
            question_analytics.comment_lines = [elem for elem in comment_lines.values()][0]
            question_analytics.import_lines = [elem for elem in import_lines.values()][0]
            question_analytics.cc = [elem for elem in cc.values()][0]
            question_analytics.method = [elem for elem in method.values()][0]
            question_analytics.operator = [elem for elem in operator.values()][0]
            question_analytics.operand = [elem for elem in operand.values()][0]
            question_analytics.unique_operator = [elem for elem in unique_operator.values()][0]
            question_analytics.unique_operand = [elem for elem in unique_operand.values()][0]
            question_analytics.vocab = [elem for elem in vocab.values()][0]
            question_analytics.size = [elem for elem in size.values()][0]
            question_analytics.vol = [elem for elem in vol.values()][0]
            question_analytics.difficulty = [elem for elem in difficulty.values()][0]
            question_analytics.effort = [elem for elem in effort.values()][0]
            question_analytics.error = [elem for elem in error.values()][0]
            question_analytics.test_time = [elem for elem in test_time.values()][0]
            question_analytics.save()
        return ParsonsQuestionAnalyticsSerializer(question_analytics).data
    if isinstance(analytics_by_question.first(), MCQSubmissionAnalytics):
        most_frequent_wrong_ans = []
        answers = MCQSubmissionAnalytics.objects \
            .filter(question=question).values_list('answer', flat=True)
        distinct_ans = answers.distinct()
        correct_ans = question.answer
        answers = list(answers)
        for ans in distinct_ans:
            if ans != correct_ans:
                most_frequent_wrong_ans.append({ans: answers.count(ans)})
        question_analytics = None
        try:
            question_analytics = MCQQuestionAnalytics.objects.get(question=question)
        except MCQQuestionAnalytics.DoesNotExist:
            MCQQuestionAnalytics.objects.create(
                question=question,
                event=event,
                course=course,
                most_frequent_wrong_ans=json.loads(json.dumps(most_frequent_wrong_ans)),
                avg_grade=avg_grade,
                grade_std_dev=grade_std_dev,
                num_respondents=num_respondents,
                avg_attempt=avg_attempt,
                attempt_std_dev=attempt_std_dev,
                median_time_spent=median_time_spent,
            )
        else:
            question_analytics.time_created = datetime.utcnow().replace(tzinfo=utc)
            question_analytics.most_frequent_wrong_ans = most_frequent_wrong_ans
            question_analytics.avg_grade = avg_grade
            question_analytics.grade_std_dev = grade_std_dev
            question_analytics.num_respondents = num_respondents
            question_analytics.avg_attempt = avg_attempt
            question_analytics.attempt_std_dev = attempt_std_dev
            question_analytics.median_time_spent = median_time_spent
            question_analytics.save()
        return MCQQuestionAnalyticsSerializer(question_analytics).data
