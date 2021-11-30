import requests
import re
from requests.auth import HTTPBasicAuth
import math

from accounts.models import MyUser
from analytics.models import SubmissionAnalytics
from course.models.java import JavaSubmission
from course.models.models import Submission, Question

from course.models.multiple_choice import MultipleChoiceSubmission
from course.models.parsons import ParsonsSubmission

unary_op_list = ["-", "++", "--", "!", "~"]
binary_op_list = ["+", "-", "*", "/", "%", "!=", "<", "<=", ">", ">=", "==", "^", "||", "|",
                  "&&", "&", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "="]


def num_lines(string):
    return 0 if len(string) == 0 else string.count('\n') + 1


def num_blank_lines(string):
    if string == "":
        return 0
    temp_list = string.split("\n")
    num = 0
    for i in temp_list:
        if i.isspace() or i == "":
            num += 1
    return num


def num_comments(string):
    temp_list = string.split("\n")
    num = 0
    for i in temp_list:
        if '//' in i or '/*' in i:
            num += 1

    return num


def num_import(string):
    temp_list = string.split("\n")
    num = 0
    for i in temp_list:
        if 'import' in i:
            num += 1

    return num


def calc_cc(string):
    num = 1
    num += string.count('if')
    num += string.count('while')
    num += string.count('for')
    num += string.count('case')
    num += string.count('&&')
    num += string.count('||')
    return num


def num_method(string):
    pattern = "(\n|\t| )(?!new|private|public)[\w]+\[?\]?(<?[\w]+?>?) +[\w]+ ?\((\w+ \w+\[\])?"
    num = len(re.findall(pattern, string))
    return num


def num_op(string):
    lines = string.split("\n")
    operator = 0
    operand = 0
    operator_list = []
    operand_list = []

    for line in lines:
        words = line.split(" ")
        if "import" in line:
            continue
        if line.strip()[0:2] == '//':
            continue
        division_duplicate = False
        if '//' in line:
            division_duplicate = True
        num_op_in_line = 0
        for i in range(len(words)):
            for bi in binary_op_list:
                if bi in words[i] and len(re.findall("^-[\w]+", words[i])) == 0:
                    # if bi not in operator_list:
                    operator_list.append(bi)
                    if bi == words[i] and 0 < i < len(words) - 1:
                        prev = words[i - 1]
                        nxt = words[i + 1]
                        operand_list.append(prev)
                        operand_list.append(nxt)
                    else:
                        split = words[i].split(bi)
                        for op in split:
                            operand_list.append(op)

                    num_op_in_line += 1
                    operator += 1
                    operand += 2
                    break
            for uni in unary_op_list:
                pattern_exception = uni + "="

                pattern_exception2 = "[^a-zA-Z\d\s]="
                neg_sign = len(re.findall("^-[\w]+", words[i]))
                rep = len(re.findall(pattern_exception2, words[i]))
                if uni in words[i] and neg_sign > 0 and pattern_exception not in words[i] and rep == 0:

                    if uni not in operator_list:
                        operator_list.append(uni)
                    split = words[i].split(uni)
                    for op in split:
                        if op != "" and op not in operand_list:
                            operand_list.append(op)

                    operator += 1
                    operand += 1
                    break

        if num_op_in_line > 1:
            num_duplicate = num_op_in_line - 1
            operand -= num_duplicate
        if division_duplicate:
            operator -= 1

    return [operator, operand, operator_list, operand_list]


def code_metrics(sub_dict):
    lines = 0
    blank_lines = 0
    comment_lines = 0
    import_lines = 0
    cc = 0
    method = 0
    operator = 0
    operand = 0
    operator_list = []
    operand_list = []
    for string in sub_dict.values():
        lines += num_lines(string)
        blank_lines += num_blank_lines(string)
        comment_lines += num_comments(string)
        import_lines += num_import(string)
        cc += calc_cc(string)
        method += num_method(string)
        op_list = num_op(string)
        operator += op_list[0]
        operand += op_list[1]
        operator_list.append(op_list[2])
        operand_list.append(op_list[3])
    return [lines, blank_lines, comment_lines, import_lines, cc, method, operator, operand, operator_list, operand_list]


def analytics():
    submissions = Submission.objects.all()
    java_list = []
    parsons_list = []
    mcq_list = []
    for submission in submissions:
        if isinstance(submission, JavaSubmission):
            java_list.append(submission)
        if isinstance(submission, ParsonsSubmission):
            parsons_list.append(submission)
        if isinstance(submission, MultipleChoiceSubmission):
            mcq_list.append(submission)

    for java_sub_obj in java_list:

        ans_file = java_sub_obj.answer_files
        res = code_metrics(ans_file)
        uqj = java_sub_obj.uqj
        submission = java_sub_obj
        question = java_sub_obj.uqj.question
        question_obj = Question.objects.get(pk=question.pk)
        user = java_sub_obj.uqj.user
        user_obj = MyUser.objects.get(pk=user.pk)
        user_id = user_obj.pk
        first_name = user_obj.first_name
        last_name = user_obj.last_name

        operator_list = res[8]
        operand_list = res[9]
        operator = res[6]
        operand = res[7]

        unique_operator = sum(len(y) for y in operator_list)
        unique_operand = sum(len(x) for x in operand_list)
        vocab = unique_operator + unique_operand
        size = operator + operand
        vol = size * math.log2(vocab)
        difficulty = unique_operator / 2 + operand / unique_operand
        effort = vol * difficulty
        error = vol / 3000
        test_time = effort / 18

        try:
            sub_analytics = SubmissionAnalytics.objects.get(submission=submission)
        except SubmissionAnalytics.DoesNotExist:
            sub_analytics = SubmissionAnalytics.objects.create(submission_type="java", uqj=uqj, submission=submission,
                                                               question=question_obj, event=java_sub_obj.question.event,
                                                               user_id=user_id,
                                                               first_name=first_name, last_name=last_name,
                                                               ans_file=ans_file, lines=res[0],
                                                               blank_lines=res[1],
                                                               comment_lines=res[2], import_lines=res[3],
                                                               cc=res[4],
                                                               method=res[5], operator=res[6],
                                                               operand=res[7], unique_operator=unique_operator,
                                                               unique_operand=unique_operand, vocab=vocab,
                                                               size=size, vol=vol, difficulty=difficulty,
                                                               effort=effort,
                                                               error=error, test_time=test_time)
    for parsons_sub_obj in parsons_list:
        ans_file = parsons_sub_obj.answer_files
        res = code_metrics(ans_file)
        uqj = parsons_sub_obj.uqj
        submission = parsons_sub_obj
        question = parsons_sub_obj.uqj.question
        question_obj = Question.objects.get(pk=question.pk)
        user = parsons_sub_obj.uqj.user
        user_obj = MyUser.objects.get(pk=user.pk)

        operator_list = res[8]
        operand_list = res[9]
        operator = res[6]
        operand = res[7]

        unique_operator = sum(len(y) for y in operator_list)
        unique_operand = sum(len(x) for x in operand_list)
        vocab = unique_operator + unique_operand
        size = operator + operand
        vol = size * math.log2(vocab)
        difficulty = unique_operator / 2 + operand / unique_operand
        effort = vol * difficulty
        error = vol / 3000
        test_time = effort / 18

        try:
            sub_analytics = SubmissionAnalytics.objects.get(submission=submission)
        except SubmissionAnalytics.DoesNotExist:
            sub_analytics = SubmissionAnalytics.objects.create(submission_type="parsons", uqj=uqj,
                                                               submission=submission,
                                                               question=question_obj, event=java_sub_obj.question.event,
                                                               user_id=user_id,
                                                               first_name=first_name, last_name=last_name,
                                                               ans_file=ans_file, lines=res[0],
                                                               blank_lines=res[1],
                                                               comment_lines=res[2], import_lines=res[3],
                                                               cc=res[4],
                                                               method=res[5], operator=res[6],
                                                               operand=res[7], unique_operator=unique_operator,
                                                               unique_operand=unique_operand, vocab=vocab,
                                                               size=size, vol=vol, difficulty=difficulty,
                                                               effort=effort,
                                                               error=error, test_time=test_time)

    for mcq_sub_obj in mcq_list:
        ans = mcq_sub_obj.answer
        uqj = mcq_sub_obj.uqj
        submission = mcq_sub_obj
        question = mcq_sub_obj.uqj.question
        question_obj = Question.objects.get(pk=question.pk)
        user = mcq_sub_obj.uqj.user
        user_obj = MyUser.objects.get(pk=user.pk)

        try:
            sub_analytics = SubmissionAnalytics.objects.get(submission=submission)
        except SubmissionAnalytics.DoesNotExist:
            sub_analytics = SubmissionAnalytics.objects.create(submission_type="mcq", uqj=uqj, submission=submission,
                                                               question=question_obj, event=java_sub_obj.question.event,
                                                               user_id=user_id,
                                                               first_name=first_name, last_name=last_name,
                                                               ans=ans)
