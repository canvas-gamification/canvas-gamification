from django.utils import timezone

from canvas.models.models import CanvasCourse, Event


def add_base_course():
    course = CanvasCourse(
        name="Test",
        url="http://canvas.ubc.ca",
        allow_registration=True,
        visible_to_students=True,
        start_date=timezone.now(),
        end_date=timezone.now() + timezone.timedelta(days=10),
    )
    course.save()
    return course


def add_base_event(course):
    event = Event(
        name="test_event",
        type="ASSIGNMENT",
        course=course,
        count_for_tokens=False,
        start_date=timezone.now(),
        end_date=timezone.now() + timezone.timedelta(days=10),
    )
    event.save()
    return event
