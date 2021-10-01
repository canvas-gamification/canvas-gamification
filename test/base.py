from django.test import TestCase, Client

from test.courses import add_base_course, add_base_event
from test.questions import add_base_category, add_base_questions
from test.users import add_base_user


class BaseTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.user = add_base_user()
        self.category = add_base_category()
        self.course = add_base_course()
        self.event = add_base_event(self.course)
        add_base_questions(self.user, self.category, self.event)
