import distance
from sklearn.cluster import AffinityPropagation
import numpy as np

from course.models.models import Submission


def levenshtein(texts):
    texts = np.asarray(texts, dtype=object)
    similarity = np.array([[distance.levenshtein(list(w1), list(w2)) for w1 in texts] for w2 in texts])
    similarity = -1 * similarity
    return similarity


def text_clustering(texts):
    texts = [t.split() for t in texts]
    similarity = levenshtein(texts)
    affprop = AffinityPropagation(
        affinity="precomputed", damping=0.5, verbose=False, random_state=0, max_iter=1_000, convergence_iter=10
    )
    affprop.fit(similarity)
    return affprop


def cluster_texts(texts):
    affprop = text_clustering(texts)
    labels = np.unique(affprop.labels_)
    texts = np.asarray(texts)
    clusters = []

    for cluster_id in labels:
        cluster = np.unique(texts[np.nonzero(affprop.labels_ == cluster_id)])
        clusters.append(
            {
                "exemplar": texts[affprop.cluster_centers_indices_[cluster_id]],
                "count": len(cluster),
                "cluster": cluster,
            }
        )

    return clusters


def get_status_messages(submissions):
    status_messages = {}

    for s in submissions.all():
        if hasattr(s, "get_status_message"):
            message = s.get_status_message()
            if message not in status_messages:
                status_messages[message] = 0
            status_messages[message] += 1

    return status_messages


def get_error_messages(submissions):
    error_messages = []

    for s in submissions.all():
        if hasattr(s, "get_failed_test_results"):
            results = s.get_failed_test_results()
            for result in results:
                error_messages.append(result["message"])

    if len(error_messages) == 0:
        return []

    return cluster_texts(error_messages)


def get_submission_stats(submissions):
    correct_submissions = submissions.filter(is_correct=True)
    partially_correct_submissions = submissions.filter(is_partially_correct=True)
    wrong_submissions = submissions.filter(is_correct=False, is_partially_correct=False)
    incorrect_submissions = partially_correct_submissions | wrong_submissions

    total = submissions.count()
    correct = correct_submissions.count()

    return {
        "total": total,
        "correct": correct,
        "partially_correct": partially_correct_submissions.count(),
        "wrong": wrong_submissions.count(),
        "success_rate": 0 if total == 0 else correct / total,
        "total_questions": submissions.values("uqj__question").distinct().count(),
        "correct_questions": correct_submissions.values("uqj__question").distinct().count(),
        "messages": get_status_messages(incorrect_submissions),
        "error_messages": get_error_messages(incorrect_submissions),
    }


def get_goal_item_stats(goal_item):
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

    return {
        "old_submissions": get_submission_stats(old_submissions),
        "submissions": get_submission_stats(submissions),
    }


def get_goal_stats(goal):
    return {goal_item.id: get_goal_item_stats(goal_item) for goal_item in goal.goal_items.all()}
