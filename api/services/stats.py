from django.contrib.contenttypes.models import ContentType

from course.models.java import JavaQuestion
from course.models.models import QuestionCategory, DIFFICULTY_CHOICES
from course.models.multiple_choice import MultipleChoiceQuestion
from course.models.parsons import ParsonsQuestion
from course.utils.utils import calculate_solved_questions, success_rate


def get_category_stats(user):
    category_stats = []

    for category in QuestionCategory.objects.all():
        for difficulty, _ in DIFFICULTY_CHOICES:
            solved, total = calculate_solved_questions(user.question_junctions, category, difficulty)
            category_stats.append(
                {
                    "category": category.id,
                    "difficulty": difficulty,
                    "questions_attempt": total,
                    "questions_solved": solved,
                    "avgSuccess": success_rate(solved, total),
                }
            )
        solved, total = calculate_solved_questions(user.question_junctions, category)
        category_stats.append(
            {
                "category": category.id,
                "difficulty": "ALL",
                "questions_attempt": total,
                "questions_solved": solved,
                "avgSuccess": success_rate(solved, total),
            }
        )

    return category_stats


def get_question_stats(user):
    mcq_ctype = ContentType.objects.get_for_model(MultipleChoiceQuestion)
    java_ctype = ContentType.objects.get_for_model(JavaQuestion)
    parsons_ctype = ContentType.objects.get_for_model(ParsonsQuestion)

    mcq_uqjs = user.question_junctions.filter(question__polymorphic_ctype=mcq_ctype)
    java_uqjs = user.question_junctions.filter(question__polymorphic_ctype=java_ctype)
    parsons_uqjs = user.question_junctions.filter(question__polymorphic_ctype=parsons_ctype)

    mcq_solved, mcq_total = calculate_solved_questions(mcq_uqjs)
    java_solved, java_total = calculate_solved_questions(java_uqjs)
    parsons_solved, parsons_total = calculate_solved_questions(parsons_uqjs)

    return {
        "mcq": {
            "questions_attempt": mcq_total,
            "questions_solved": mcq_solved,
            "avgSuccess": success_rate(mcq_solved, mcq_total),
        },
        "java": {
            "questions_attempt": java_total,
            "questions_solved": java_solved,
            "avgSuccess": success_rate(java_solved, java_total),
        },
        "parsons": {
            "questions_attempt": parsons_total,
            "questions_solved": parsons_solved,
            "avgSuccess": success_rate(parsons_solved, parsons_total),
        },
    }


def get_challenge_stats(user):
    return {
        "challenges_completed": 0,
    }


def get_goal_stats(user):
    return {
        "goals_completed": 0,
    }
