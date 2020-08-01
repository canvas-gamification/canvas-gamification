from course.exceptions import SubmissionException
from course.models.models import MultipleChoiceQuestion, MultipleChoiceSubmission, CheckboxQuestion, JavaQuestion, \
    JavaSubmission, Submission
from course.models.parsons_question import ParsonsQuestion, ParsonsSubmission
from course.utils.utils import get_user_question_junction


def get_submission_class(question):
    if isinstance(question, MultipleChoiceQuestion):
        return MultipleChoiceSubmission
    if isinstance(question, CheckboxQuestion):
        return MultipleChoiceSubmission
    if isinstance(question, JavaQuestion):
        return JavaSubmission
    if isinstance(question, ParsonsQuestion):
        return ParsonsSubmission

    raise SubmissionException("Internal Server Error, please contact developers")


def submit_solution(question, user, solution):
    uqj = get_user_question_junction(user, question)

    if uqj.submissions.filter(answer=solution).exists():
        raise SubmissionException("You have already submitted this answer!")

    if not uqj.is_allowed_to_submit:
        raise SubmissionException("You are not allowed to submit")

    SubmissionClass = get_submission_class(question)

    submission = SubmissionClass()
    submission.answer = solution
    submission.uqj = uqj

    submission.submit()
    submission.save()
    uqj.save()

    return submission


def get_all_submissions(question, user):
    if not user.is_authenticated:
        return Submission.objects.none()

    uqj = get_user_question_junction(user, question)
    return uqj.submissions.all()
