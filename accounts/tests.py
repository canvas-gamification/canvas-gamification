from accounts.models import MyUser
from test.base import BaseTestCase


class AccountsTestCase(BaseTestCase):
    def test_login(self):
        self.client.login(username="test_user", password="aaaaaaaaa")

    def test_teacher(self):
        user = MyUser.objects.get()
        self.assertFalse(user.is_teacher)
