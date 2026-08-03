"""Baseline tests for the accounts app and the account-related API flows.

Covers: registration -> activation -> login, password reset, reCAPTCHA validation,
``MyUser`` model behaviour (tokens / roles / community JWT) and the e-mail side
effects of ``ContactUs.save()``, ``send_question_report_email`` and
``course_create_email``.

These tests lock in *current* behaviour (Python 3.8 / Django 3.0 / DRF 3.11) so the
Python 3.14 / Django 6.0 upgrade can be checked for behaviour preservation. They
deliberately avoid asserting on Django/DRF-generated wording (password validators,
e-mail template prose) because that drifts between versions.
"""

import re
from unittest import mock

import jwt
from django.conf import settings as django_settings
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import MyUser, STUDENT, TEACHER
from accounts.utils.email_functions import (
    account_activation_token_generator,
    activate_user,
    course_create_email,
    reset_password_token_generator,
    send_question_report_email,
    verify_reset,
)
from general.models.action import Action, ActionStatus, ActionVerb
from general.models.contact_us import ContactUs
from general.models.question_report import QuestionReport
from test.baseline.fixtures_accounts import (
    ORIGIN,
    OTHER_STRONG_PASSWORD,
    STRONG_PASSWORD,
    make_category,
    make_course,
    make_mcq_question,
    make_teacher,
    make_user,
)
from utils.recaptcha import validate_recaptcha

ACTIVATION_LINK_RE = re.compile(r"/accounts/activate/([^/\s]+)/([^/\s]+)/")
RESET_LINK_RE = re.compile(r"/accounts/reset-password/([^/\s]+)/([^/\s]+)/")

# The from-address used by every outbound e-mail (settings.EMAIL_ACTIVATION in DEBUG).
EXPECTED_FROM = "test@gamification.com"
# Hard-coded recipient of the contact-us / question-report / course-create e-mails.
EXPECTED_STAFF_RECIPIENT = "bowen.hui@ubc.ca"

REGISTRATION_PAYLOAD = {
    "email": "newcomer@example.com",
    "first_name": "New",
    "last_name": "Comer",
    "nickname": "newbie",
    "password": STRONG_PASSWORD,
    "password2": STRONG_PASSWORD,
    "recaptcha_key": "dummy-recaptcha-token",
}


def _url(name, *args, **kwargs):
    return reverse(name, args=args, kwargs=kwargs)


class RecaptchaPassingMixin(object):
    """Make ``validate_recaptcha`` succeed without touching the network.

    NOTE: Django's test runner forces ``settings.DEBUG = False``, so the
    ``if settings.DEBUG: return True`` short-circuit in ``utils/recaptcha.py`` never
    fires under test. Every reCAPTCHA-protected endpoint therefore really does call
    ``requests.post(settings.RECAPTCHA_URL, ...)`` during tests -- which today fails
    fast (RECAPTCHA_URL is ``""``) and makes the request 400. Patching is mandatory.
    """

    def setUp(self):
        super(RecaptchaPassingMixin, self).setUp()
        ok = mock.Mock()
        ok.json.return_value = {"success": True}
        patcher = mock.patch("utils.recaptcha.requests.post", return_value=ok)
        self.recaptcha_post = patcher.start()
        self.addCleanup(patcher.stop)


class RegistrationActivationLoginTest(RecaptchaPassingMixin, APITestCase):
    """Registration -> activation e-mail -> activation -> login round trip."""

    def _register(self, **overrides):
        payload = dict(REGISTRATION_PAYLOAD)
        payload.update(overrides)
        return self.client.post(_url("api:register-list"), payload, HTTP_ORIGIN=ORIGIN)

    def test_registration_response_shape_and_inactive_user(self):
        response = self._register()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # write_only fields (password / password2 / recaptcha_key) are not echoed back.
        self.assertEqual(set(response.data.keys()), {"email", "first_name", "last_name", "nickname"})

        user = MyUser.objects.get(email=REGISTRATION_PAYLOAD["email"])
        # username is set from the e-mail address by UserRegistrationSerializer.create()
        self.assertEqual(user.username, REGISTRATION_PAYLOAD["email"])
        self.assertFalse(user.is_active)
        self.assertEqual(user.role, STUDENT)
        self.assertTrue(user.check_password(STRONG_PASSWORD))

    def test_registration_sends_one_activation_email(self):
        self._register()

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "Activate your account.")
        self.assertEqual(message.to, [REGISTRATION_PAYLOAD["email"]])
        self.assertEqual(message.from_email, EXPECTED_FROM)
        # The HTTP_ORIGIN header is what the activation link is built from.
        self.assertIn(ORIGIN, message.body)
        self.assertIsNotNone(ACTIVATION_LINK_RE.search(message.body))

    def test_registration_requires_http_origin_header(self):
        # KNOWN-BUG: accounts/utils/email_functions.py:53 reads request.META["HTTP_ORIGIN"]
        # directly, so a registration POST without an Origin header raises an unhandled
        # KeyError (HTTP 500) *after* the user row has already been committed.
        with self.assertRaises(KeyError):
            self.client.post(_url("api:register-list"), REGISTRATION_PAYLOAD)

        self.assertTrue(MyUser.objects.filter(email=REGISTRATION_PAYLOAD["email"]).exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_duplicate_email_rejected(self):
        self._register()
        mail.outbox = []
        response = self._register()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_mismatch_rejected(self):
        response = self._register(password2=OTHER_STRONG_PASSWORD)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(MyUser.objects.filter(email=REGISTRATION_PAYLOAD["email"]).exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_missing_required_fields_rejected(self):
        response = self.client.post(_url("api:register-list"), {}, HTTP_ORIGIN=ORIGIN)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            set(response.data.keys()),
            {"email", "first_name", "last_name", "nickname", "password", "password2", "recaptcha_key"},
        )

    def test_full_round_trip_register_activate_login(self):
        self._register()
        uid, token = ACTIVATION_LINK_RE.search(mail.outbox[0].body).groups()

        login_url = _url("api:token-auth")
        credentials = {"username": REGISTRATION_PAYLOAD["email"], "password": STRONG_PASSWORD}

        # Inactive users cannot obtain a token.
        self.assertEqual(self.client.post(login_url, credentials).status_code, status.HTTP_400_BAD_REQUEST)

        activate_response = self.client.post(
            _url("api:register-activate"), {"uuid": uid, "token": token}, format="json"
        )
        self.assertEqual(activate_response.status_code, status.HTTP_200_OK)

        user = MyUser.objects.get(email=REGISTRATION_PAYLOAD["email"])
        self.assertTrue(user.is_active)

        login_response = self.client.post(login_url, credentials)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(login_response.data.keys()),
            {
                "id",
                "token",
                "first_name",
                "last_name",
                "username",
                "tokens",
                "role",
                "is_teacher",
                "is_student",
                "has_consent",
                "community_jwt",
            },
        )
        self.assertEqual(login_response.data["token"], Token.objects.get(user=user).key)
        # MyUser.tokens is None when the user has no Action rows at all, but the login
        # view creates the LOGGED_IN action *before* reading user.tokens, so a first
        # login already reports 0.0 rather than None.
        self.assertEqual(login_response.data["tokens"], 0.0)
        self.assertTrue(Action.objects.filter(actor=user, verb=ActionVerb.LOGGED_IN).exists())
        self.assertEqual(Action.objects.filter(actor=user, verb=ActionVerb.LOGGED_IN).count(), 1)

    def test_activation_token_is_single_use(self):
        self._register()
        uid, token = ACTIVATION_LINK_RE.search(mail.outbox[0].body).groups()
        activate_url = _url("api:register-activate")

        self.assertEqual(
            self.client.post(activate_url, {"uuid": uid, "token": token}, format="json").status_code,
            status.HTTP_200_OK,
        )
        # is_active is part of the token hash body, so flipping it invalidates the token.
        second = self.client.post(activate_url, {"uuid": uid, "token": token}, format="json")
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activation_with_tampered_token_returns_400(self):
        self._register()
        uid, token = ACTIVATION_LINK_RE.search(mail.outbox[0].body).groups()
        tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

        response = self.client.post(_url("api:register-activate"), {"uuid": uid, "token": tampered}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Activation link is invalid.", str(response.data))
        self.assertFalse(MyUser.objects.get(email=REGISTRATION_PAYLOAD["email"]).is_active)

    def test_activation_with_garbage_uid_returns_400(self):
        response = self.client.post(
            _url("api:register-activate"), {"uuid": "not-base64", "token": "nope"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activation_with_missing_body_returns_400(self):
        response = self.client.post(_url("api:register-activate"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activation_with_expired_token_returns_400(self):
        # The generator's own expiry setting has moved between Django versions
        # (PASSWORD_RESET_TIMEOUT_DAYS -> PASSWORD_RESET_TIMEOUT), so pin the endpoint's
        # contract rather than the timeout mechanics: a token the generator rejects
        # must produce a 400 and leave the account inactive.
        self._register()
        uid, token = ACTIVATION_LINK_RE.search(mail.outbox[0].body).groups()

        with mock.patch.object(account_activation_token_generator, "check_token", return_value=False):
            response = self.client.post(_url("api:register-activate"), {"uuid": uid, "token": token}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(MyUser.objects.get(email=REGISTRATION_PAYLOAD["email"]).is_active)


class TokenGeneratorTest(APITestCase):
    """Behaviour (not hash internals) of the custom TokenGenerator singletons.

    The hash body currently uses ``six.text_type``; the upgrade replaces it with
    ``str``, which must not change any of the behaviour asserted here.
    """

    def setUp(self):
        super().setUp()
        self.user = make_user(username="tokgen", email="tokgen@example.com")

    def test_token_round_trips_for_its_own_user(self):
        token = account_activation_token_generator.make_token(self.user)
        self.assertTrue(account_activation_token_generator.check_token(self.user, token))

    def test_activation_and_reset_generators_are_interchangeable(self):
        # Both module-level singletons are plain TokenGenerator() instances, so a token
        # minted by one validates against the other.
        token = account_activation_token_generator.make_token(self.user)
        self.assertTrue(reset_password_token_generator.check_token(self.user, token))

    def test_token_is_rejected_for_a_different_user(self):
        other = make_user(username="tokgen2", email="tokgen2@example.com")
        token = account_activation_token_generator.make_token(self.user)
        self.assertFalse(account_activation_token_generator.check_token(other, token))

    def test_token_invalidated_by_is_active_change(self):
        token = account_activation_token_generator.make_token(self.user)
        self.user.is_active = not self.user.is_active
        self.user.save()
        self.assertFalse(account_activation_token_generator.check_token(self.user, token))

    def test_token_invalidated_by_last_login_change(self):
        token = account_activation_token_generator.make_token(self.user)
        self.user.last_login = timezone.now()
        self.user.save()
        self.assertFalse(account_activation_token_generator.check_token(self.user, token))

    def test_activate_user_helper_returns_none_on_bad_input(self):
        self.assertIsNone(activate_user(None, None))
        self.assertIsNone(activate_user("garbage", "garbage"))

    def test_verify_reset_bumps_last_login_and_single_uses_the_token(self):
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = reset_password_token_generator.make_token(self.user)

        verified = verify_reset(uid, token)
        self.assertIsNotNone(verified)
        self.assertIsNotNone(MyUser.objects.get(pk=self.user.pk).last_login)

        # last_login is part of the hash body, so the same token no longer verifies.
        self.assertIsNone(verify_reset(uid, token))


class PasswordResetFlowTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user(username="resetter", email="resetter@example.com")
        # Registration leaves accounts inactive; the reset flow re-activates them.
        self.user.is_active = False
        self.user.save()

    def _send_reset_email(self, email=None):
        return self.client.post(
            _url("api:reset-password-send-email"),
            {"email": email if email is not None else self.user.email},
            HTTP_ORIGIN=ORIGIN,
        )

    def test_send_email_success_shape(self):
        response = self._send_reset_email()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "Reset your password")
        self.assertEqual(message.to, [self.user.email])
        # NOTE: sent from EMAIL_ACTIVATION, not EMAIL_PASSWORD_RESET (they happen to
        # be equal in DEBUG, but the source really does use EMAIL_ACTIVATION).
        self.assertEqual(message.from_email, EXPECTED_FROM)
        self.assertIsNotNone(RESET_LINK_RE.search(message.body))
        self.assertTrue(Action.objects.filter(actor=self.user, verb=ActionVerb.COMPLETED).exists())

    def test_send_email_unknown_email_returns_404(self):
        response = self._send_reset_email(email="nobody@example.com")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_email_missing_email_returns_404(self):
        response = self.client.post(_url("api:reset-password-send-email"), {}, HTTP_ORIGIN=ORIGIN)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_send_email_requires_http_origin_header(self):
        # KNOWN-BUG: same unguarded request.META["HTTP_ORIGIN"] read as registration
        # (accounts/utils/email_functions.py:93).
        with self.assertRaises(KeyError):
            self.client.post(_url("api:reset-password-send-email"), {"email": self.user.email})

    def test_reset_round_trip(self):
        self._send_reset_email()
        uid, token = RESET_LINK_RE.search(mail.outbox[0].body).groups()

        response = self.client.post(
            _url("api:reset-password-list"),
            {"uid": uid, "token": token, "password": OTHER_STRONG_PASSWORD, "password2": OTHER_STRONG_PASSWORD},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Every serializer field is write_only, so the response body is empty.
        self.assertEqual(set(response.data.keys()), set())

        user = MyUser.objects.get(pk=self.user.pk)
        self.assertTrue(user.check_password(OTHER_STRONG_PASSWORD))
        self.assertFalse(user.check_password(STRONG_PASSWORD))
        # The reset flow also re-activates the account.
        self.assertTrue(user.is_active)
        self.assertTrue(Action.objects.filter(actor=user, verb=ActionVerb.UPDATED).exists())

    def test_reset_token_is_single_use(self):
        self._send_reset_email()
        uid, token = RESET_LINK_RE.search(mail.outbox[0].body).groups()
        payload = {
            "uid": uid,
            "token": token,
            "password": OTHER_STRONG_PASSWORD,
            "password2": OTHER_STRONG_PASSWORD,
        }

        first = self.client.post(_url("api:reset-password-list"), payload, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        # verify_reset() bumped last_login, which is part of the token hash body.
        second = self.client.post(_url("api:reset-password-list"), payload, format="json")
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_with_tampered_token_returns_400(self):
        self._send_reset_email()
        uid, token = RESET_LINK_RE.search(mail.outbox[0].body).groups()
        tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

        response = self.client.post(
            _url("api:reset-password-list"),
            {"uid": uid, "token": tampered, "password": OTHER_STRONG_PASSWORD, "password2": OTHER_STRONG_PASSWORD},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(MyUser.objects.get(pk=self.user.pk).check_password(STRONG_PASSWORD))

    def test_reset_with_mismatched_passwords_returns_400(self):
        self._send_reset_email()
        uid, token = RESET_LINK_RE.search(mail.outbox[0].body).groups()

        response = self.client.post(
            _url("api:reset-password-list"),
            {"uid": uid, "token": token, "password": OTHER_STRONG_PASSWORD, "password2": STRONG_PASSWORD},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(MyUser.objects.get(pk=self.user.pk).check_password(STRONG_PASSWORD))

    def test_reset_missing_fields_returns_400_with_all_field_errors(self):
        response = self.client.post(_url("api:reset-password-list"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(set(response.data.keys()), {"uid", "token", "password", "password2"})


@override_settings(DEBUG=False, RECAPTCHA_URL="https://recaptcha.invalid/verify", RECAPTCHA_KEY="secret-key")
class RecaptchaTest(APITestCase):
    """reCAPTCHA accepted / rejected paths. ``requests`` is always patched: no network."""

    @staticmethod
    def _response(payload):
        fake = mock.Mock()
        fake.json.return_value = payload
        return fake

    def test_validate_recaptcha_accepted(self):
        with mock.patch("utils.recaptcha.requests.post", return_value=self._response({"success": True})) as post:
            self.assertTrue(validate_recaptcha("a-token"))

        post.assert_called_once_with(
            "https://recaptcha.invalid/verify", {"secret": "secret-key", "response": "a-token"}
        )

    def test_validate_recaptcha_rejected(self):
        with mock.patch("utils.recaptcha.requests.post", return_value=self._response({"success": False})):
            self.assertFalse(validate_recaptcha("a-token"))

    def test_validate_recaptcha_missing_success_key_is_false(self):
        with mock.patch("utils.recaptcha.requests.post", return_value=self._response({})):
            self.assertFalse(validate_recaptcha("a-token"))

    def test_validate_recaptcha_request_exception_is_false(self):
        from requests.exceptions import RequestException

        with mock.patch("utils.recaptcha.requests.post", side_effect=RequestException("boom")):
            self.assertFalse(validate_recaptcha("a-token"))

    @override_settings(DEBUG=True)
    def test_validate_recaptcha_short_circuits_in_debug(self):
        with mock.patch("utils.recaptcha.requests.post") as post:
            self.assertTrue(validate_recaptcha("anything"))
        post.assert_not_called()

    def test_registration_accepted_when_recaptcha_succeeds(self):
        with mock.patch("utils.recaptcha.requests.post", return_value=self._response({"success": True})):
            response = self.client.post(_url("api:register-list"), REGISTRATION_PAYLOAD, HTTP_ORIGIN=ORIGIN)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MyUser.objects.filter(email=REGISTRATION_PAYLOAD["email"]).exists())
        self.assertEqual(len(mail.outbox), 1)

    def test_registration_rejected_when_recaptcha_fails(self):
        with mock.patch("utils.recaptcha.requests.post", return_value=self._response({"success": False})):
            response = self.client.post(_url("api:register-list"), REGISTRATION_PAYLOAD, HTTP_ORIGIN=ORIGIN)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("recaptcha_key", response.data)
        self.assertFalse(MyUser.objects.filter(email=REGISTRATION_PAYLOAD["email"]).exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_contact_us_accepted_when_recaptcha_succeeds(self):
        payload = {
            "fullname": "Ada Lovelace",
            "email": "ada@example.com",
            "comment": "Hello there",
            "recaptcha_key": "tok",
        }
        with mock.patch("utils.recaptcha.requests.post", return_value=self._response({"success": True})):
            response = self.client.post(_url("api:contact-us-list"), payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ContactUs.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_contact_us_rejected_when_recaptcha_fails(self):
        payload = {
            "fullname": "Ada Lovelace",
            "email": "ada@example.com",
            "comment": "Hello there",
            "recaptcha_key": "tok",
        }
        with mock.patch("utils.recaptcha.requests.post", return_value=self._response({"success": False})):
            response = self.client.post(_url("api:contact-us-list"), payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("recaptcha_key", response.data)
        self.assertEqual(ContactUs.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)


class MyUserModelTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user(username="modeluser", email="modeluser@example.com")

    def _action(self, token_change):
        Action.create_action(
            actor=self.user,
            description="baseline",
            token_change=token_change,
            status=ActionStatus.COMPLETE,
            verb=ActionVerb.EVALUATED,
        )

    def test_tokens_is_none_without_actions(self):
        self.assertIsNone(self.user.tokens)

    def test_tokens_sums_action_token_change(self):
        self._action(1.5)
        self._action(2.5)
        self._action(0)
        self.assertEqual(self.user.tokens, 4.0)

    def test_tokens_can_be_negative(self):
        self._action(2)
        self._action(-5)
        self.assertEqual(self.user.tokens, -3.0)

    def test_tokens_only_counts_own_actions(self):
        other = make_user(username="modeluser2", email="modeluser2@example.com")
        self._action(7)
        Action.create_action(
            actor=other,
            description="baseline",
            token_change=100,
            status=ActionStatus.COMPLETE,
            verb=ActionVerb.EVALUATED,
        )
        self.assertEqual(self.user.tokens, 7.0)
        self.assertEqual(other.tokens, 100.0)

    def test_role_properties(self):
        teacher = make_teacher(username="modelteacher", email="modelteacher@example.com")

        self.assertEqual(self.user.role, STUDENT)
        self.assertFalse(self.user.is_teacher)
        self.assertTrue(self.user.is_student)

        self.assertEqual(teacher.role, TEACHER)
        self.assertTrue(teacher.is_teacher)
        self.assertFalse(teacher.is_student)

    def test_name_and_consent_properties(self):
        self.assertTrue(self.user.has_name)
        self.assertTrue(self.user.has_complete_profile)
        self.assertFalse(self.user.has_consent)

        nameless = make_user(username="nameless", email="nameless@example.com", first_name="")
        self.assertFalse(nameless.has_name)
        self.assertFalse(nameless.has_complete_profile)

    def test_anonymous_user_is_not_teacher(self):
        from accounts.models import MyAnonymousUser

        self.assertFalse(MyAnonymousUser().is_teacher)

    @override_settings(COMMUNITY_JWT_PRIVATE_KEY="baseline-jwt-secret")
    def test_community_jwt_claims(self):
        token = self.user.community_jwt
        # PyJWT 2.x returns a str; PyJWT 1.x returned bytes. Accept whatever decodes.
        # The app still emits an int "sub" (MyUser.community_jwt is unchanged and the
        # encoder still accepts it); only PyJWT's *decoder* became strict in 2.10, which
        # rejects a non-string "sub" with InvalidSubjectError. Turn that check off so this
        # test keeps verifying the real payload.
        claims = jwt.decode(token, "baseline-jwt-secret", algorithms=["HS256"], options={"verify_sub": False})

        self.assertEqual(
            claims,
            {
                "sub": self.user.id,
                "email": self.user.email,
                "name": self.user.get_full_name(),
            },
        )

    @override_settings(COMMUNITY_JWT_PRIVATE_KEY="baseline-jwt-secret")
    def test_community_jwt_falls_back_to_username_and_email(self):
        user = MyUser(username="fallback-user", email="", first_name="", last_name="", role=STUDENT)
        user.save()

        # verify_sub=False: the app still emits an int "sub"; only PyJWT >= 2.10's decoder
        # became strict about "sub" being a string.
        claims = jwt.decode(
            user.community_jwt, "baseline-jwt-secret", algorithms=["HS256"], options={"verify_sub": False}
        )
        self.assertEqual(claims["email"], "fallback-user")
        self.assertEqual(claims["name"], "")

    @override_settings(COMMUNITY_JWT_PRIVATE_KEY="baseline-jwt-secret")
    def test_community_jwt_rejects_wrong_secret(self):
        token = self.user.community_jwt
        with self.assertRaises(jwt.InvalidSignatureError):
            jwt.decode(token, "not-the-secret", algorithms=["HS256"])

    def test_community_jwt_uses_the_configured_settings_key(self):
        # Round-trip against whatever COMMUNITY_JWT_PRIVATE_KEY is configured (defaults to
        # SECRET_KEY when unset).  verify_sub=False: the app still emits an int "sub"; only
        # PyJWT >= 2.10's decoder became strict about "sub" being a string.
        claims = jwt.decode(
            self.user.community_jwt,
            django_settings.COMMUNITY_JWT_PRIVATE_KEY,
            algorithms=["HS256"],
            options={"verify_sub": False},
        )
        self.assertEqual(claims["sub"], self.user.id)

    def test_user_consent_is_student_property(self):
        from accounts.models import UserConsent

        consent = UserConsent.objects.create(user=self.user, consent=True)
        self.assertTrue(consent.is_student)
        self.assertTrue(self.user.has_consent)

    def test_user_consent_is_student_crashes_when_user_is_null(self):
        # KNOWN-BUG: UserConsent.user is nullable (SET_NULL) but the is_student property
        # dereferences it unconditionally (accounts/models.py:133-135).
        from accounts.models import UserConsent

        consent = UserConsent.objects.create(user=None, consent=True)
        with self.assertRaises(AttributeError):
            consent.is_student


class EmailSideEffectTest(APITestCase):
    """Subject / recipient / from-address of the three 'staff notification' e-mails."""

    def setUp(self):
        super().setUp()
        self.user = make_user(username="emailer", email="emailer@example.com")

    def test_contact_us_save_sends_email(self):
        contact = ContactUs(fullname="Grace Hopper", email="grace@example.com", comment="A bug!")
        contact.save()

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "Contact Us Question")
        self.assertEqual(message.to, [EXPECTED_STAFF_RECIPIENT])
        self.assertEqual(message.from_email, EXPECTED_FROM)
        self.assertIn("Grace Hopper", message.body)
        self.assertIn("grace@example.com", message.body)
        self.assertIn("A bug!", message.body)

    def test_contact_us_save_sends_an_email_every_time(self):
        contact = ContactUs(fullname="Grace Hopper", email="grace@example.com", comment="A bug!")
        contact.save()
        contact.comment = "Another bug!"
        contact.save()

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(ContactUs.objects.count(), 1)

    def test_send_question_report_email(self):
        category = make_category()
        question = make_mcq_question(author=self.user, category=category)
        report = QuestionReport.objects.create(
            user=self.user, question=question, report="TYPO_TEXT", report_details="Typo in line 2"
        )

        send_question_report_email(report)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "A question was reported")
        self.assertEqual(message.to, [EXPECTED_STAFF_RECIPIENT])
        self.assertEqual(message.from_email, EXPECTED_FROM)
        self.assertIn(str(question.id), message.body)
        self.assertIn("Typo in line 2", message.body)
        self.assertIn(self.user.email, message.body)

    def test_course_create_email(self):
        teacher = make_teacher(username="course-owner", email="course-owner@example.com")
        course = make_course(instructor=teacher)

        course_create_email(course)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "A course was created")
        self.assertEqual(message.to, [EXPECTED_STAFF_RECIPIENT])
        self.assertEqual(message.from_email, EXPECTED_FROM)
        self.assertIn(str(course.id), message.body)
        self.assertIn(teacher.email, message.body)
