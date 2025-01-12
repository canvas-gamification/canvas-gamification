from django.contrib.contenttypes.models import ContentType

from course.models.java import JavaQuestion
from course.models.models import Submission
from course.models.multiple_choice import MultipleChoiceQuestion
from course.models.parsons import ParsonsQuestion
from course.services.question import get_solved_questions_ratio


def get_submission_bugs(submissions):
    all_bugs = {}
    all_patterns = {}

    for submission in submissions.all():
        if not hasattr(submission, "bugs"):
            continue
        data = submission.bugs
        for bug in data["bugs"]:
            if bug["type"] not in all_bugs:
                all_bugs[bug["type"]] = bug
                all_bugs[bug["type"]]["count"] = 0
            all_bugs[bug["type"]]["count"] += 1
        for pattern in data["patterns"]:
            if pattern["type"] not in all_patterns:
                all_patterns[pattern["type"]] = pattern

    return {
        "bugs": all_bugs.values(),
        "patterns": all_patterns.values(),
    }


def get_submission_stats(submissions):
    correct_submissions = submissions.filter(is_correct=True)
    partially_correct_submissions = submissions.filter(is_partially_correct=True)
    wrong_submissions = submissions.filter(is_correct=False, is_partially_correct=False)
    incorrect_submissions = partially_correct_submissions | wrong_submissions

    total = submissions.count()
    correct = correct_submissions.count()

    total_questions = submissions.values("uqj__question").distinct().count()
    correct_questions = correct_submissions.values("uqj__question").distinct().count()

    return {
        "total": total,
        "correct": correct,
        "partially_correct": partially_correct_submissions.count(),
        "wrong": wrong_submissions.count(),
        "success_rate": 0 if total == 0 else correct / total,
        "total_questions": total_questions,
        "correct_questions": correct_questions,
        "questions_success_rate": 0 if total_questions == 0 else correct_questions / total_questions,
        "bugs": get_submission_bugs(incorrect_submissions),
    }


def get_goal_item_conclusion(goal_item, stats):
    ratio = get_solved_questions_ratio(goal_item.goal.course_reg.user, goal_item.category_id, goal_item.difficulty)
    category_name = goal_item.category.full_name

    if ratio < 0.2:
        if goal_item.goal.claimed:
            return {
                "status": "NO_DATA",
                "message": "To make a recommendation, "
                           "more questions need to be solved as the number of questions in the goal is insufficient.",
            }
        else:
            return {
                "status": "NO_DATA",
                "message": "To make a recommendation, "
                           "more questions need to be solved as the current data is insufficient.",
            }
    if ratio < 0.8 and (stats["success_rate"] < 0.8 or stats["questions_success_rate"] < 0.8):
        return {
            "status": "NEED_PRACTICE",
            "message": f"You need to solve more questions in {category_name} to improve your understanding of the "
                       f"topic. Practice is essential for mastering any subject.",
        }
    if not goal_item.goal.claimed:
        return {
            "status": "MASTER",
            "message": f"Good work! Finish up the remaining questions to solidify your skills.",
        }
    if goal_item.difficulty != "HARD":
        return {
            "status": "MASTER",
            "message": f"Good work! It's time to start solving harder questions in {category_name} "
                       f"to improve your skills.",
        }
    return {
        "status": "MASTER",
        "message": "Good job! Now, let's move on to the next categories and continue building your skills.",
    }


def get_goal_item_stats(goal_item):
    mcq_ctype = ContentType.objects.get_for_model(MultipleChoiceQuestion)
    java_ctype = ContentType.objects.get_for_model(JavaQuestion)
    parsons_ctype = ContentType.objects.get_for_model(ParsonsQuestion)

    submissions = Submission.objects.filter(
        uqj__user=goal_item.goal.course_reg.user,
        uqj__question__category=goal_item.category,
        uqj__question__event=None,
        submission_time__gt=goal_item.goal.start_date,
        submission_time__lt=goal_item.goal.end_date,
    )

    old_submissions = Submission.objects.filter(
        uqj__user=goal_item.goal.course_reg.user,
        uqj__question__category=goal_item.category,
        uqj__question__event=None,
        submission_time__lt=goal_item.goal.start_date,
    )

    if goal_item.difficulty:
        submissions = submissions.filter(uqj__question__difficulty=goal_item.difficulty)
        old_submissions = old_submissions.filter(uqj__question__difficulty=goal_item.difficulty)

    all_stats = get_submission_stats(submissions | old_submissions)

    return {
        "mcq": {
            "submissions": get_submission_stats(submissions.filter(uqj__question__polymorphic_ctype=mcq_ctype)),
            "old_submissions": get_submission_stats(old_submissions.filter(uqj__question__polymorphic_ctype=mcq_ctype)),
        },
        "java": {
            "submissions": get_submission_stats(submissions.filter(uqj__question__polymorphic_ctype=java_ctype)),
            "old_submissions": get_submission_stats(
                old_submissions.filter(uqj__question__polymorphic_ctype=java_ctype)
            ),
        },
        "parsons": {
            "submissions": get_submission_stats(submissions.filter(uqj__question__polymorphic_ctype=parsons_ctype)),
            "old_submissions": get_submission_stats(
                old_submissions.filter(uqj__question__polymorphic_ctype=parsons_ctype)
            ),
        },
        "all": {
            "submissions": get_submission_stats(submissions),
            "old_submissions": get_submission_stats(old_submissions),
        },
        "conclusion": get_goal_item_conclusion(goal_item, all_stats),
    }


def get_goal_stats(goal):
    return {goal_item.id: get_goal_item_stats(goal_item) for goal_item in goal.goal_items.all()}
