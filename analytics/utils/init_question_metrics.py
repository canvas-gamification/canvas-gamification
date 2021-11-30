
from analytics.models import SubmissionAnalytics, QuestionAnalytics



def init():

    sub_analytics = dict()

    wrong_answer_dict = {}
    for obj in SubmissionAnalytics.objects.all():
        sub_analytics.setdefault(obj.question.id, []).append(obj)
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
            avg_grade += item.submission.grade

            question = item.question
            event = item.event

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

            if item.submission.is_correct:
                correct_sub += 1
            elif item.submission.answer in wrong_answers:
                if item.submission_type == 'mcq':
                    wrong_answers[item.submission.answer] += 1
                else:
                    reason_wrong = item.submission.get_decoded_stderr()
            else:
                if item.submission_type == 'mcq':
                    wrong_answers[item.submission.answer] = 1
                else:
                    reason_wrong = item.submission.get_decoded_stderr()

        wrong_ans = 0
        max = 0
        for key in wrong_answers:
            if wrong_answers[key] > max:
                wrong_ans = key
                max = wrong_answers[key]

        try:
            question_metrics = QuestionAnalytics.objects.get(question=question)
        except QuestionAnalytics.DoesNotExist:
            question_metrics = QuestionAnalytics.objects.create(number_submission=number_submission,
                                                                question=question, event=event,
                                                                avg_grade=avg_grade/number_submission,
                                                                correct_rate=correct_sub/number_submission,
                                                                frequently_wrong_ans=wrong_ans,
                                                                frequently_wrong_reason=reason_wrong,
                                                                lines=lines/number_submission,
                                                                blank_lines=blank_lines/number_submission,
                                                                comment_lines=comment_lines/number_submission,
                                                                import_lines=import_lines/number_submission,
                                                                cc=cc/number_submission,
                                                                method=method/number_submission,
                                                                operator=operator/number_submission,
                                                                operand=operand/number_submission,
                                                                unique_operator=unique_operator/number_submission,
                                                                unique_operand=unique_operand/number_submission,
                                                                vocab=vocab/number_submission,
                                                                size=size/number_submission, vol=vol/number_submission,
                                                                difficulty=difficulty/number_submission,
                                                                effort=effort/number_submission,
                                                                error=error/number_submission,
                                                                test_time=test_time/number_submission)


