from django.test import TestCase
# Create your tests here.
from django.utils import timezone

from canvas.models import CanvasCourse


class MockCourseTestCase(TestCase):

    def setUp(self) -> None:
        self.course = CanvasCourse(
            mock=True,
            name="Test",
            url="http://canvas.ubc.ca",
            course_id=1,
            token="test token",

            allow_registration=True,
            visible_to_students=True,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=10),

            verification_assignment_group_name="test",
            verification_assignment_name="test",
            bonus_assignment_group_name="test",
        )
        self.course.save()

    def test_mock_course(self):
        self.assertIsNotNone(self.course.verification_assignment_id)
        self.assertIsNotNone(self.course.bonus_assignment_group_id)
        self.assertIsNotNone(self.course.verification_assignment_group_id)

        self.assertEqual(self.course.course.attributes.get('name'), 'Mock Course')
        self.assertEqual(self.course.guess_user('firstname lastname')[0], self.course.course.get_users()[0].name)
