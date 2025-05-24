def get_student_gradebook(student, course):
    results = []

    for event in course.events.filter(type__in=["ASSIGNMENT", "EXAM"]):
        uqjs = student.user.question_junctions.filter(question__event_id__in=[event.id])
        results.append(
            {
                "grade": sum(uqjs.values_list("tokens_received", flat=True)),
                "total": event.total_tokens,
                "name": student.full_name,
                "event_name": event.name,
                "question_details": [
                    {
                        "title": uqj.question.title,
                        "question_grade": uqj.tokens_received,
                        "question_value": uqj.question.token_value,
                        "attempts": uqj.submissions.count(),
                        "max_attempts": uqj.question.max_submission_allowed,
                    }
                    for uqj in uqjs
                ],
            }
        )

    return results


def get_course_gradebook(course):
    students = course.verified_course_registration.filter(registration_type="STUDENT")
    results = []

    for student in students:
        results += get_student_gradebook(student, course)

    return results
