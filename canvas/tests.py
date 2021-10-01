# Create your tests here.

from test.base import BaseTestCase


class MockCourseTestCase(BaseTestCase):

    def test_mock_course(self):
        self.assertIsNotNone(self.course.verification_assignment_id)
        self.assertIsNotNone(self.course.bonus_assignment_group_id)
        self.assertIsNotNone(self.course.verification_assignment_group_id)

        self.assertEqual(self.course.course.attributes.get('name'), 'Mock Course')
        self.assertEqual(self.course.guess_user('firstname lastname')[0], self.course.course.get_users()[0].name)
