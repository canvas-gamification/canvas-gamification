from course.models.models import Submission, Question
from course.models.multiple_choice import MultipleChoiceQuestion
import re


def _get_status_messages(submissions):
    status_messages = {}

    for s in submissions.all():
        if hasattr(s, "get_status_message"):
            message = s.get_status_message()
            if message not in status_messages:
                status_messages[message] = 0
            status_messages[message] += 1

    return status_messages


def _get_error_messages(submissions):
    error_messages = {}

    for s in submissions.all():
        if hasattr(s, "get_failed_test_results"):
            results = s.get_failed_test_results()
            for result in results:
                message = result["message"]
                if message not in error_messages:
                    error_messages[message] = 0
                error_messages[message] += 1

    return error_messages


def _get_submission_status(submissions):
    return {
        "Correct": submissions.filter(is_correct=True).count(),
        "Partially Correct": submissions.filter(is_correct=False, is_partially_correct=True).count(),
        "Incorrect": submissions.filter(is_correct=False, is_partially_correct=False).count(),
    }


def get_question_stats(question):
    submissions = Submission.objects.filter(uqj__question=question)

    answers = {}
    if isinstance(question, MultipleChoiceQuestion):
        for submission in submissions:
            answer = submission.uqj.get_rendered_choices()[submission.answer]
            if answer not in answers:
                answers[answer] = 0
            answers[answer] += 1

    return {
        "question": {
            "title": question.title,
        },
        "has_variables": len(question.variables) > 0,
        "answers": answers,
        "error_messages": _get_error_messages(submissions),
        "submissions": _get_submission_status(submissions),
        "status_messages": _get_status_messages(submissions),
        "total_submissions": submissions.count(),
    }


def get_event_stats(event):
    return [get_question_stats(question) for question in event.question_set.all()]


def set_featured(event):
    event.course.events.update(featured=False)
    event.featured = True
    event.save()


def add_question_set(event, category_id, difficulty, number_of_questions):
    questions = Question.objects.filter(
        event=None,
        course=None,
        is_verified=True,
        question_status=Question.CREATED,
        category_id=category_id,
        difficulty=difficulty,
    )[:number_of_questions]

    question_titles = [question["title"] for question in event.question_set.values("title")]
    question_titles.sort()
    print(question_titles)

    if len(question_titles) == 0:
        index = 0  # in case items is empty, and you need it after the loop
        for index, question in enumerate(questions, start=1):
            question.copy_to_event(event, str(index))
        return

    available_titles = get_available_question_titles(question_titles)
    if len(available_titles) == 0:
        title = len(question_titles) + 1
        index = 0
        for index, question in enumerate(questions, start=0):
            question.copy_to_event(event, str(index + title))
    else:
        for index, question in enumerate(questions):
            max_idx_of_available_titles = len(available_titles) - 1
            if index > max_idx_of_available_titles:
                question.copy_to_event(event, str(int(question_titles[-1]) + (index - max_idx_of_available_titles)))
            else:
                question.copy_to_event(event, str(available_titles[index]))


# TODO: This is based on the assumption that the question names are stored in numbers...hmmmm
def get_available_question_titles(question_titles: list):
    available_titles = []
    diff = 1

    to_delete_titles = []
    # modify question_titiles so it only contains pure numbers titles. Titles w/o numbers will be removed
    for idx, question_title in enumerate(question_titles):
        if has_numbers(question_title):
            print('in-if', question_title)
            question_titles[idx] = scrape_number_from_string(question_title)
            print('in-if', question_titles[idx])
        else:
            print('in-else', question_title)
            to_delete_titles.append(question_titles[idx])

    for e in to_delete_titles:
        question_titles.remove(e)

    question_titles = [int(title) for title in question_titles]
    question_titles.sort()
    print(question_titles)

    if question_titles[0] != 1:
        while question_titles[0] > diff:
            available_titles.append(str(diff))
            diff += 1
    print(available_titles)
    for i in range(0, len(question_titles)):
        if question_titles[i] - 1 != diff:
            while question_titles[i] > diff + i:
                available_titles.append(str(diff + i))
                diff += 1

    print(available_titles)
    return available_titles


def has_numbers(string):
    return any(char.isdigit() for char in string)


def scrape_number_from_string(string):
    return re.search('[0-9]+', string).group()
