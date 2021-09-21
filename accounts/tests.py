from accounts.forms import SignupForm
from accounts.models import MyUser
from test.base import BaseTestCase


class AccountsTestCase(BaseTestCase):

    def test_login(self):
        self.client.login(username="test_user", password="aaaaaaaaa")

    def test_teacher(self):
        user = MyUser.objects.get()
        self.assertFalse(user.is_teacher)


class AccountFormsTestCase(BaseTestCase):
    def test_recaptcha(self):
        form = SignupForm({
            'email': 'a@a.com',
            'username': '123',
            'password1': 'aaaaaaaa',
            'password2': 'aaaaaaaa',
            'consent': True,
        })

        self.assertFalse(form.is_valid())
        self.assertEquals(form.cleaned_data['email'], form.cleaned_data['username'])
        self.assertEquals(list(form.non_field_errors())[0], "reCaptcha should be validate")

    def test_recaptcha_debug(self):
        form = SignupForm({
            'email': 'a@a.com',
            'username': '123',
            'password1': 'aaaaaaaa',
            'password2': 'aaaaaaaa',
            'consent': True,
        })

        with self.settings(DEBUG=True):
            self.assertTrue(form.is_valid())
