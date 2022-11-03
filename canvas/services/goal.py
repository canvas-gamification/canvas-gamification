from course.models.models import Submission


def get_goal_item_stats(goal_item):
    submissions = Submission.objects.filter(
        uqj__user=goal_item.goal.course_reg.user,
        uqj__question__category=goal_item.category,
        uqj__question__event=None,
        submission_time__gt=goal_item.goal.start_date,
        submission_time__lt=goal_item.goal.end_date,
    )

    if goal_item.difficulty:
        submissions = submissions.filter(uqj__question__difficulty=goal_item.difficulty)

    return {
        "total": submissions.count(),
        "correct": submissions.filter(is_correct=True).count(),
        "partially_correct": submissions.filter(is_partially_correct=True).count(),
        "wrong": submissions.filter(is_correct=False, is_partially_correct=False).count(),
    }


def get_goal_stats(goal):
    return {goal_item.id: get_goal_item_stats(goal_item) for goal_item in goal.goal_items.all()}
