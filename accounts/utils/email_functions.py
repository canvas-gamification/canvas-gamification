import six
from datetime import datetime

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from accounts.models import MyUser
from canvas_gamification import settings


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user.is_active) + six.text_type(
            user.last_login)


account_activation_token_generator = TokenGenerator()
reset_password_token_generator = TokenGenerator()


def activate_user(uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = MyUser.objects.get(pk=uid)
        if account_activation_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return user
    except(TypeError, ValueError, OverflowError, AttributeError, MyUser.DoesNotExist):
        return None
    return None


def send_activation_email(request, user):
    mail_subject = 'Activate your account.'
    message = render_to_string('accounts/activation_email.html', {
        'user': user,
        'domain': request.META['HTTP_ORIGIN'],
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token_generator.make_token(user),
    })
    to_email = user.email
    email = EmailMessage(
        mail_subject, message, from_email=settings.EMAIL_ACTIVATION, to=[to_email]
    )
    email.send()


def verify_reset(uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = MyUser.objects.get(pk=uid)
        if reset_password_token_generator.check_token(user, token):
            user.last_login = datetime.now()
            user.save()
            return user
    except(TypeError, ValueError, OverflowError, AttributeError, MyUser.DoesNotExist):
        return None
    return None


def send_reset_email(request, user):
    mail_subject = 'Reset your password'
    message = render_to_string('accounts/password_reset_email.html', {
        'user': user,
        'domain': request.META['HTTP_ORIGIN'],
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': reset_password_token_generator.make_token(user),
    })
    to_email = user.email
    email = EmailMessage(
        mail_subject, message, from_email=settings.EMAIL_ACTIVATION, to=[to_email]
    )
    email.send()


def send_contact_us_email(fullname, email, comment):
    mail_subject = 'Contact Us Question'
    message = render_to_string('accounts/contact_us_email.html', {
        'fullname': fullname,
        'email': email,
        'comment': comment,
    })
    to_email = 'carsonricca28@gmail.com'
    email = EmailMessage(
        mail_subject, message, from_email=settings.EMAIL_ACTIVATION, to=[to_email]
    )
    email.send()
