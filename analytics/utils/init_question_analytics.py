from analytics.models import JavaSubmissionAnalytics, ParsonsSubmissionAnalytics, MCQSubmissionAnalytics
from analytics.models.java import JavaQuestionAnalytics
from analytics.models.mcq import MCQQuestionAnalytics
from analytics.models.models import SubmissionAnalytics, QuestionAnalytics
from analytics.models.parsons import ParsonsQuestionAnalytics
from course.models.models import Submission
from course.models.multiple_choice import MultipleChoiceSubmission
from polymorphic.utils import reset_polymorphic_ctype


def init():
    sub_analytics = dict()

    wrong_answer_dict = {}
    for obj in SubmissionAnalytics.objects.all():
        sub_analytics.setdefault(obj.question, []).append(obj)
        print(type(obj))
    for key in sub_analytics:

        number_submission = 0
        avg_grade = 0
        correct_sub = 0
        lines = 0
        blank_lines = 0
        comment_lines = 0
        import_lines = 0
        cc = 0
        method = 0
        operator = 0
        operand = 0
        unique_operator = 0
        unique_operand = 0
        vocab = 0
        size = 0
        vol = 0
        difficulty = 0
        effort = 0
        error = 0
        test_time = 0
        question = None
        event = None

        wrong_answers = dict()
        reason_wrong = ""

        for item in sub_analytics[key]:

            number_submission += 1
            avg_grade += Submission.objects.get(pk=item.submission).grade

            question = item.question
            event = item.event

            if isinstance(item, JavaSubmissionAnalytics) or isinstance(item, ParsonsSubmissionAnalytics):
                lines += item.lines
                blank_lines += item.blank_lines
                comment_lines += item.comment_lines
                import_lines += item.import_lines
                cc += item.cc
                method += item.method
                operator += item.operator
                operand += item.operand
                unique_operator += item.unique_operator
                unique_operand += item.unique_operand
                vocab += item.vocab
                size += item.size
                vol += item.vol
                difficulty += item.difficulty
                effort += item.effort
                error += item.error
                test_time += item.test_time

            submission_obj = Submission.objects.get(pk=item.submission)
            if submission_obj.is_correct:
                correct_sub += 1
            elif submission_obj.answer in wrong_answers:
                if isinstance(submission_obj, MultipleChoiceSubmission):
                    wrong_answers[submission_obj.answer] += 1
                else:
                    reason_wrong = submission_obj.get_decoded_stderr()
            else:
                if isinstance(submission_obj, MultipleChoiceSubmission):
                    wrong_answers[submission_obj.answer] = 1
                else:
                    reason_wrong = submission_obj.get_decoded_stderr()

        wrong_ans = ""
        max = 0
        for key in wrong_answers:
            if wrong_answers[key] > max:
                wrong_ans = key
                max = wrong_answers[key]

        if isinstance(item, JavaSubmissionAnalytics):
            print("java")
            try:
                question_analytics = JavaQuestionAnalytics.objects.get(question=question)
            except QuestionAnalytics.DoesNotExist:
                question_analytics = JavaQuestionAnalytics \
                    .objects.create(number_submission=number_submission,
                                    question=question, event=event,
                                    avg_grade=avg_grade / number_submission,
                                    correct_rate=correct_sub / number_submission,
                                    frequent_wrong_ans=wrong_ans,
                                    frequent_wrong_reason=reason_wrong,
                                    lines=lines / number_submission,
                                    blank_lines=blank_lines / number_submission,
                                    comment_lines=comment_lines / number_submission,
                                    import_lines=import_lines / number_submission,
                                    cc=cc / number_submission,
                                    method=method / number_submission,
                                    operator=operator / number_submission,
                                    operand=operand / number_submission,
                                    unique_operator=unique_operator / number_submission,
                                    unique_operand=unique_operand / number_submission,
                                    vocab=vocab / number_submission,
                                    size=size / number_submission,
                                    vol=vol / number_submission,
                                    difficulty=difficulty / number_submission,
                                    effort=effort / number_submission,
                                    error=error / number_submission,
                                    test_time=test_time / number_submission)

                reset_polymorphic_ctype(QuestionAnalytics, JavaQuestionAnalytics, ignore_existing=True)
            else:
                question_analytics.number_submission = number_submission
                question_analytics.avg_grade = avg_grade / number_submission
                question_analytics.correct_rate = correct_sub / number_submission
                question_analytics.frequent_wrong_ans = wrong_ans
                question_analytics.frequent_wrong_reason = reason_wrong
                question_analytics.lines = lines / number_submission
                question_analytics.blank_lines = blank_lines / number_submission
                question_analytics.comment_lines = comment_lines / number_submission
                question_analytics.import_lines = import_lines / number_submission
                question_analytics.cc = cc / number_submission
                question_analytics.method = method / number_submission
                question_analytics.operator = operator / number_submission
                question_analytics.operand = operand / number_submission
                question_analytics.unique_operator = unique_operator / number_submission
                question_analytics.unique_operand = unique_operand / number_submission
                question_analytics.vocab = vocab / number_submission
                question_analytics.size = size / number_submission
                question_analytics.vol = vol / number_submission
                question_analytics.difficulty = difficulty / number_submission
                question_analytics.effort = effort / number_submission
                question_analytics.error = error / number_submission
                question_analytics.test_time = test_time / number_submission
                question_analytics.save()
        if isinstance(item, ParsonsSubmissionAnalytics):
            print("parsons")
            try:
                question_analytics = ParsonsQuestionAnalytics.objects.get(question=question)
            except QuestionAnalytics.DoesNotExist:
                question_analytics = ParsonsQuestionAnalytics \
                    .objects.create(number_submission=number_submission,
                                    question=question, event=event,
                                    avg_grade=avg_grade / number_submission,
                                    correct_rate=correct_sub / number_submission,
                                    frequent_wrong_ans=wrong_ans,
                                    frequent_wrong_reason=reason_wrong,
                                    lines=lines / number_submission,
                                    blank_lines=blank_lines / number_submission,
                                    comment_lines=comment_lines / number_submission,
                                    import_lines=import_lines / number_submission,
                                    cc=cc / number_submission,
                                    method=method / number_submission,
                                    operator=operator / number_submission,
                                    operand=operand / number_submission,
                                    unique_operator=unique_operator / number_submission,
                                    unique_operand=unique_operand / number_submission,
                                    vocab=vocab / number_submission,
                                    size=size / number_submission,
                                    vol=vol / number_submission,
                                    difficulty=difficulty / number_submission,
                                    effort=effort / number_submission,
                                    error=error / number_submission,
                                    test_time=test_time / number_submission)
                reset_polymorphic_ctype(QuestionAnalytics, ParsonsQuestionAnalytics, ignore_existing=True)
            else:
                question_analytics.number_submission = number_submission
                question_analytics.avg_grade = avg_grade / number_submission
                question_analytics.correct_rate = correct_sub / number_submission
                question_analytics.frequent_wrong_ans = wrong_ans
                question_analytics.frequent_wrong_reason = reason_wrong
                question_analytics.lines = lines / number_submission
                question_analytics.blank_lines = blank_lines / number_submission
                question_analytics.comment_lines = comment_lines / number_submission
                question_analytics.import_lines = import_lines / number_submission
                question_analytics.cc = cc / number_submission
                question_analytics.method = method / number_submission
                question_analytics.operator = operator / number_submission
                question_analytics.operand = operand / number_submission
                question_analytics.unique_operator = unique_operator / number_submission
                question_analytics.unique_operand = unique_operand / number_submission
                question_analytics.vocab = vocab / number_submission
                question_analytics.size = size / number_submission
                question_analytics.vol = vol / number_submission
                question_analytics.difficulty = difficulty / number_submission
                question_analytics.effort = effort / number_submission
                question_analytics.error = error / number_submission
                question_analytics.test_time = test_time / number_submission
                question_analytics.save()

        if isinstance(item, MCQSubmissionAnalytics):
            print("mcq")
            try:
                question_analytics = MCQQuestionAnalytics.objects.get(question=question)
            except QuestionAnalytics.DoesNotExist:
                question_analytics = MCQQuestionAnalytics \
                    .objects.create(number_submission=number_submission,
                                    question=question, event=event,
                                    avg_grade=avg_grade / number_submission,
                                    correct_rate=correct_sub / number_submission,
                                    frequent_wrong_ans=wrong_ans,
                                    frequent_wrong_reason=reason_wrong)
                reset_polymorphic_ctype(QuestionAnalytics, MCQQuestionAnalytics, ignore_existing=True)
            else:
                question_analytics.number_submission = number_submission
                question_analytics.avg_grade = avg_grade / number_submission
                question_analytics.correct_rate = correct_sub / number_submission
                question_analytics.frequent_wrong_ans = wrong_ans
                question_analytics.frequent_wrong_reason = reason_wrong
                question_analytics.save()
