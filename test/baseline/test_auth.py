"""
Baseline tests for authentication.

Covers ``POST /api/api-token-auth/`` (``api/views/auth.py``) end to end plus the
two globally configured DRF authenticators (Basic + Token,
``settings.REST_FRAMEWORK``).  Assertions are on status codes, response key sets
and our own model state -- never on Django/DRF error strings, which drift
between versions.
"""

import base64

import jwt
from django.conf import settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from general.models.action import Action, ActionObjectType, ActionStatus, ActionVerb
from test.baseline import factories

LOGIN_RESPONSE_KEYS = {
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
}

# An endpoint that only needs IsAuthenticated, used to prove a credential works.
PROTECTED_URL_NAME = "api:user-stats-list"


class TokenAuthTest(APITestCase):
    def setUp(self):
        super(TokenAuthTest, self).setUp()
        self.url = reverse("api:token-auth")
        self.student = factories.make_student("auth_student", first_name="Sam", last_name="Study", nickname="sam")
        self.teacher = factories.make_teacher("auth_teacher", first_name="Terry", last_name="Teach")

    def login(self, username, password):
        return self.client.post(self.url, {"username": username, "password": password}, format="json")

    # -- happy path --------------------------------------------------------
    def test_login_returns_the_full_key_set(self):
        response = self.login("auth_student", factories.PASSWORD)
        self.assertEqual(200, response.status_code)
        self.assertEqual(LOGIN_RESPONSE_KEYS, set(response.data.keys()))

    def test_login_values_for_a_student(self):
        response = self.login("auth_student", factories.PASSWORD)
        data = response.data
        self.assertEqual(self.student.id, data["id"])
        self.assertEqual("auth_student", data["username"])
        self.assertEqual("Sam", data["first_name"])
        self.assertEqual("Study", data["last_name"])
        self.assertEqual("Student", data["role"])
        self.assertFalse(data["is_teacher"])
        self.assertTrue(data["is_student"])
        self.assertFalse(data["has_consent"])
        self.assertEqual(Token.objects.get(user=self.student).key, data["token"])

    def test_login_values_for_a_teacher(self):
        response = self.login("auth_teacher", factories.PASSWORD)
        self.assertEqual("Teacher", response.data["role"])
        self.assertTrue(response.data["is_teacher"])
        self.assertFalse(response.data["is_student"])

    def test_has_consent_is_true_once_a_consent_row_exists(self):
        factories.make_consent(self.student)
        self.assertTrue(self.login("auth_student", factories.PASSWORD).data["has_consent"])

    def test_tokens_is_zero_on_a_first_login_because_the_login_action_counts(self):
        # MyUser.tokens sums Action.token_change and is None when the user has no
        # actions at all -- but create_login_action() runs BEFORE the response is
        # built, so the very first login already reports 0.0 rather than None.
        self.assertIsNone(self.student.tokens)
        response = self.login("auth_student", factories.PASSWORD)
        self.assertEqual(0, response.data["tokens"])

    def test_tokens_reflects_the_action_ledger(self):
        factories.make_action(self.student, token_change=3.5)
        factories.make_action(self.student, token_change=-1.5)
        self.assertEqual(2.0, self.login("auth_student", factories.PASSWORD).data["tokens"])

    def test_community_jwt_is_signed_with_the_configured_key(self):
        response = self.login("auth_student", factories.PASSWORD)
        payload = jwt.decode(
            response.data["community_jwt"],
            settings.COMMUNITY_JWT_PRIVATE_KEY,
            algorithms=["HS256"],
        )
        self.assertEqual(
            {"sub": self.student.id, "email": self.student.email, "name": "Sam Study"},
            payload,
        )

    def test_login_creates_exactly_one_login_action(self):
        self.assertEqual(0, Action.objects.count())
        self.login("auth_student", factories.PASSWORD)
        self.assertEqual(1, Action.objects.count())
        action = Action.objects.get()
        self.assertEqual(self.student, action.actor)
        self.assertEqual("User logged in", action.description)
        self.assertEqual(0, action.token_change)
        self.assertEqual(ActionStatus.COMPLETE, action.status)
        self.assertEqual(ActionVerb.LOGGED_IN, action.verb)
        self.assertEqual(ActionObjectType.USER, action.object_type)
        self.assertEqual(self.student.id, action.object_id)

    def test_logging_in_twice_reuses_the_token_and_logs_a_second_action(self):
        first = self.login("auth_student", factories.PASSWORD)
        second = self.login("auth_student", factories.PASSWORD)
        self.assertEqual(first.data["token"], second.data["token"])
        self.assertEqual(1, Token.objects.filter(user=self.student).count())
        self.assertEqual(2, Action.objects.filter(verb=ActionVerb.LOGGED_IN).count())

    # -- failures ----------------------------------------------------------
    def test_wrong_password_is_a_400_and_mints_no_token_and_logs_no_action(self):
        response = self.login("auth_student", "definitely-not-the-password")
        self.assertEqual(400, response.status_code)
        self.assertEqual({"non_field_errors"}, set(response.data.keys()))
        self.assertEqual(0, Token.objects.count())
        self.assertEqual(0, Action.objects.count())

    def test_unknown_username_is_a_400(self):
        response = self.login("nobody_at_all", factories.PASSWORD)
        self.assertEqual(400, response.status_code)
        self.assertEqual({"non_field_errors"}, set(response.data.keys()))

    def test_inactive_user_is_a_400(self):
        inactive = factories.make_student("auth_inactive", is_active=False)
        response = self.login(inactive.username, factories.PASSWORD)
        self.assertEqual(400, response.status_code)
        self.assertEqual({"non_field_errors"}, set(response.data.keys()))

    def test_missing_fields_is_a_400_naming_both_fields(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(400, response.status_code)
        self.assertEqual({"username", "password"}, set(response.data.keys()))

    def test_empty_password_is_a_400(self):
        response = self.client.post(self.url, {"username": "auth_student", "password": ""}, format="json")
        self.assertEqual(400, response.status_code)
        self.assertEqual({"password"}, set(response.data.keys()))

    def test_get_is_not_allowed(self):
        self.assertEqual(405, self.client.get(self.url).status_code)


class CredentialsTest(APITestCase):
    """The two authenticators configured in settings.REST_FRAMEWORK."""

    def setUp(self):
        super(CredentialsTest, self).setUp()
        self.student = factories.make_student("cred_student")
        self.protected_url = reverse(PROTECTED_URL_NAME)

    def token_for(self, user):
        response = self.client.post(
            reverse("api:token-auth"),
            {"username": user.username, "password": factories.PASSWORD},
            format="json",
        )
        self.assertEqual(200, response.status_code)
        return response.data["token"]

    def test_no_credentials_is_401(self):
        response = self.client.get(self.protected_url)
        self.assertEqual(401, response.status_code)
        # BasicAuthentication is first in the list, so it owns the challenge.
        self.assertEqual('Basic realm="api"', response["WWW-Authenticate"])

    def test_the_returned_token_authenticates_a_follow_up_request(self):
        key = self.token_for(self.student)
        client = factories.api_client()
        client.credentials(HTTP_AUTHORIZATION="Token " + key)
        response = client.get(self.protected_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {"token_stats", "challenge_stats", "goal_stats", "question_stats", "category_stats"},
            set(response.data.keys()),
        )

    def test_a_bogus_token_is_401(self):
        client = factories.api_client()
        client.credentials(HTTP_AUTHORIZATION="Token 0000000000000000000000000000000000000000")
        self.assertEqual(401, client.get(self.protected_url).status_code)

    def test_a_token_without_the_keyword_is_401(self):
        client = factories.api_client()
        client.credentials(HTTP_AUTHORIZATION=self.token_for(self.student))
        self.assertEqual(401, client.get(self.protected_url).status_code)

    def test_basic_auth_works(self):
        raw = "{}:{}".format(self.student.username, factories.PASSWORD)
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        client = factories.api_client()
        client.credentials(HTTP_AUTHORIZATION="Basic " + encoded)
        self.assertEqual(200, client.get(self.protected_url).status_code)

    def test_basic_auth_with_a_wrong_password_is_401(self):
        raw = "{}:{}".format(self.student.username, "wrong")
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        client = factories.api_client()
        client.credentials(HTTP_AUTHORIZATION="Basic " + encoded)
        self.assertEqual(401, client.get(self.protected_url).status_code)

    def test_session_auth_is_not_configured(self):
        """
        SessionAuthentication is deliberately absent from
        DEFAULT_AUTHENTICATION_CLASSES, so a Django login does not authenticate
        API calls.
        """
        self.assertEqual(
            [
                "rest_framework.authentication.BasicAuthentication",
                "rest_framework.authentication.TokenAuthentication",
            ],
            settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"],
        )
        self.assertNotIn("DEFAULT_PERMISSION_CLASSES", settings.REST_FRAMEWORK)
        self.assertTrue(self.client.login(username=self.student.username, password=factories.PASSWORD))
        self.assertEqual(401, self.client.get(self.protected_url).status_code)
