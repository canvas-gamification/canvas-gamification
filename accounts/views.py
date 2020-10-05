from django.contrib import messages
from django.contrib.auth import login, views as auth_views
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render
# Create your views here.
from django.urls import reverse_lazy
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.views.generic import UpdateView

from accounts.forms import SignupForm, UserProfileForm, LoginForm, PasswordChangeForm
from accounts.models import MyUser
from accounts.utils.email_functions import send_activation_email, account_activation_token_generator
from canvas_gamification import settings


class LoginView(auth_views.LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            send_activation_email(request, user)
            return render(request, 'accounts/message.html', {
                'title': "Sign Up Successful",
                'message': "Thank you for signing up. An activation link is sent to your email. Please Activate your "
                           "account using that link",
            })
    else:
        form = SignupForm()
    return render(request, 'accounts/register.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = MyUser.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, MyUser.DoesNotExist):
        user = None
    if user is not None and account_activation_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return render(request, 'accounts/activation_confirm.html')
    else:
        return render(request, 'accounts/message.html', {
            'title': "Something went wrong",
            'message': 'Activation link is invalid!',
        })


class UserProfileView(UpdateView):
    model = MyUser
    template_name = 'accounts/profile.html'
    form_class = UserProfileForm
    success_url = None

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Profile Updated Successfully!")
        return reverse_lazy('homepage')


class PasswordChangeView(auth_views.PasswordChangeView):
    success_url = reverse_lazy('accounts:password_change_done')
    template_name = 'accounts/password_change.html'
    form_class = PasswordChangeForm


def password_change_done_view(request):
    return render(request, 'accounts/message.html', {
        'title': "Password Changed",
        'message': 'Your password has been successfully changed!',
    })


def forgot_password_view(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(subject_template_name='account/password_reset_email_subject.txt',
                      email_template_name='account/password_reset_email.html',
                      from_email=settings.EMAIL_PASSWORD_RESET,
                      request=request)
            return render(request, 'accounts/message.html', {
                'title': "Password Reset Email Sent",
                'message': 'Your password reset request has been sent to your email, '
                           'please follow the further instruction in your email',
            })
    else:
        form = PasswordResetForm()
    return render(request, 'accounts/forgot.html', {'form': form})


def password_reset_view(request, uidb64, token):
    def get_user():
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = MyUser.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, MyUser.DoesNotExist):
            user = None
        if user is not None and default_token_generator.check_token(user, token):
            return user
        return None

    def bad_token():
        return render(request, 'accounts/message.html', {
            'title': "Something Went Wrong :(",
            'message': 'Your token in invalid',
        })

    if request.method == 'POST':
        user = get_user()
        if not user:
            return bad_token()

        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            if not user.is_active:
                user.is_active = True
                user.save()
            return render(request, 'accounts/message.html', {
                'title': "Your Password Has Been Reset",
                'message': 'Your password has been reset successfully, please login with your new password',
            })
    else:
        user = get_user()
        if not user:
            return bad_token()
        form = SetPasswordForm(user)
    return render(request, 'accounts/password_reset.html', {'form': form})
