import requests
from django import forms
from django.contrib.auth import password_validation, get_user_model
from django.contrib.auth.forms import UserCreationForm, UsernameField, UserChangeForm
from django.utils.translation import gettext_lazy as _

from canvas_gamification.settings import RECAPTCHA_URL, RECAPTCHA_KEY


class SignupForm(UserCreationForm):

    username = UsernameField(
        label=_("Username"),
        strip=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    email = forms.EmailField(
        label=_("Email"),
        max_length=200,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )

    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text=password_validation.password_validators_help_text_html(),
    )

    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
    )

    def is_valid(self):
        response = self.data['g-recaptcha-response']

        r = requests.post(RECAPTCHA_URL, {
            'secret': RECAPTCHA_KEY,
            'response': response,
        })

        data = r.json()

        if not data['success']:
            self.add_error(None, 'reCaptcha should be validate')
            return False

        return super(SignupForm, self).is_valid()

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password1', 'password2')


class UserProfileForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = ['username', 'first_name', 'last_name', 'email']

    username = UsernameField(
        label=_("Username"),
        strip=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    email = forms.EmailField(
        label=_("Email"),
        max_length=200,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )

    first_name = forms.CharField(
        label=_("First Name"),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    last_name = forms.CharField(
        label=_("Last Name"),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    password = None