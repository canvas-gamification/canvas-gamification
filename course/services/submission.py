import json

from course.exceptions import SubmissionException
from course.models.java import JavaSubmission
from course.models.multiple_choice import MultipleChoiceSubmission
from course.models.parsons import ParsonsSubmission
from course.utils.utils import get_user_question_junction


def submit_java_solution(question, user, answer_dict):
    if isinstance(answer_dict, str):
        answer_dict = json.loads(answer_dict)

    uqj = get_user_question_junction(user, question)

    if not uqj.is_allowed_to_submit:
        raise SubmissionException("You are not allowed to submit")

    submission = JavaSubmission()
    submission.answer_files = answer_dict
    submission.uqj = uqj

    for input_file in uqj.get_input_files():
        if "hidden" in input_file.keys() and input_file["hidden"]:
            hidden_file = {input_file["name"]: input_file["template"]}
            submission.answer_files.update(hidden_file)

    submission.submit()
    submission.save()
    uqj.save()

    return submission


def submit_mcq_solution(question, user, solution):
    uqj = get_user_question_junction(user, question)

    if not user.is_teacher and not question.is_practice and uqj.submissions.filter(answer=solution).exists():
        raise SubmissionException("You have already submitted this answer!")

    if not uqj.is_allowed_to_submit:
        raise SubmissionException("You are not allowed to submit")

    submission = MultipleChoiceSubmission()
    submission.answer = solution
    submission.uqj = uqj

    submission.submit()
    submission.save()
    uqj.save()

    return submission


def submit_parsons_solution(question, user, solution):
    uqj = get_user_question_junction(user, question)

    if not uqj.is_allowed_to_submit:
        raise SubmissionException("You are not allowed to submit")

    submission = ParsonsSubmission()
    submission.answer_files = solution
    submission.uqj = uqj

    submission.submit()
    submission.save()
    uqj.save()

    return submission
