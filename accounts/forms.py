import requests
from django import forms
from django.contrib.auth import password_validation, forms as auth_forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from accounts.models import MyUser
from canvas_gamification.settings import RECAPTCHA_URL, RECAPTCHA_KEY


class PasswordWidget(forms.PasswordInput):
    template_name = 'accounts/widgets/password.html'


def add_class_to_widget(widget, name):
    if 'class' not in widget.attrs:
        widget.attrs.update({'class': ''})
    widget.attrs.update({'class': widget.attrs['class'] + ' ' + name})


def add_bootstrap_validation(form):
    for field in form.fields:
        print(field, form.has_error(field))
        if form.has_error(field):
            add_class_to_widget(form.fields[field].widget, 'is-invalid')
        else:
            add_class_to_widget(form.fields[field].widget, 'is-valid')


class LoginForm(auth_forms.AuthenticationForm):
    is_login = forms.BooleanField(
        widget=forms.HiddenInput,
        initial=True,
    )
    username = auth_forms.UsernameField(widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'}))
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=PasswordWidget(attrs={'autocomplete': 'current-password', 'class': 'form-control'}),
    )

    def is_valid(self):
        valid = super().is_valid()
        add_bootstrap_validation(self)
        return valid


class SignupForm(auth_forms.UserCreationForm):
    class Meta:
        model = MyUser
        fields = ('username', 'email', 'password1', 'password2')

    username = auth_forms.UsernameField(
        label=_("Username"),
        strip=False,
        initial="123",
        widget=forms.HiddenInput(attrs={'class': 'form-control'}),
    )

    email = forms.EmailField(
        label=_("Email"),
        max_length=200,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )

    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=PasswordWidget(attrs={'class': 'form-control'}),
        help_text=password_validation.password_validators_help_text_html(),
    )

    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=PasswordWidget(attrs={'class': 'form-control'}),
        strip=False,
    )

    consent = forms.BooleanField(
        label="",
        widget=forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
        required=True,
    )

    def clean(self):
        data = super().clean()
        if 'email' in data:
            data['username'] = data['email']
        return data

    def is_valid(self):
        response = self.data.get('g-recaptcha-response', None)

        r = requests.post(RECAPTCHA_URL, {
            'secret': RECAPTCHA_KEY,
            'response': response,
        })

        data = r.json()

        if not data['success']:
            self.add_error(None, 'reCaptcha should be validate')
            return False

        valid = super(SignupForm, self).is_valid()
        add_bootstrap_validation(self)
        return valid


class UserProfileForm(auth_forms.UserChangeForm):
    class Meta:
        model = MyUser
        fields = ['first_name', 'last_name', 'email']

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

    def is_valid(self):
        valid = super().is_valid()
        add_bootstrap_validation(self)
        return valid


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    old_password = forms.CharField(
        label=_("Old password"),
        strip=False,
        widget=PasswordWidget(attrs={'autocomplete': 'current-password', 'autofocus': True, 'class': 'form-control'}),
    )

    new_password1 = forms.CharField(
        label=_("New password"),
        widget=PasswordWidget(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=PasswordWidget(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )

    def is_valid(self):
        valid = super().is_valid()
        add_bootstrap_validation(self)
        return valid
