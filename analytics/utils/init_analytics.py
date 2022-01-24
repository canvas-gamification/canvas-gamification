import re
import math
import time

from accounts.models import MyUser
from analytics.models import JavaSubmissionAnalytics, ParsonsSubmissionAnalytics, MCQSubmissionAnalytics
from analytics.models.models import SubmissionAnalytics
from course.models.java import JavaSubmission
from course.models.models import Submission
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


def calc_halstead(operator_list, operand_list, operator, operand):
    unique_operator = sum(len(y) for y in operator_list)
    unique_operand = sum(len(x) for x in operand_list)
    vocab = unique_operator + unique_operand
    size = operator + operand
    if size == 0 or vocab == 0:
        return [0, 0, 0, 0, 0, 0, 0, 0, 0]
    vol = size * math.log2(vocab)
    difficulty = unique_operator / 2 + operand / unique_operand
    effort = vol * difficulty
    error = vol / 3000
    test_time = effort / 18

    return [unique_operator, unique_operand, vocab, size, vol, difficulty, effort, error, test_time]


class SubmissionAnalyticsObj:
    def __init__(self, submission_code):
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
        halstead = [0, 0, 0, 0, 0, 0, 0, 0, 0]

        for string in submission_code.values():
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
            if string is not None or string != '':
                halstead = calc_halstead(operator_list, operand_list, operator, operand)

        unique_operator = halstead[0]
        unique_operand = halstead[1]
        vocab = halstead[2]
        size = halstead[3]
        vol = halstead[4]
        difficulty = halstead[5]
        effort = halstead[6]
        error = halstead[7]
        test_time = halstead[8]

        self.lines = lines
        self.blank_lines = blank_lines
        self.comment_lines = comment_lines
        self.imported_lines = import_lines
        self.cc = cc
        self.method = method
        self.operator = operator
        self.operand = operand
        self.unique_operator = unique_operator
        self.unique_operand = unique_operand
        self.vocab = vocab
        self.size = size
        self.vol = vol
        self.difficulty = difficulty
        self.effort = effort
        self.error = error
        self.test_time = test_time
