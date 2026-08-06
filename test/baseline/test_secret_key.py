"""SECRET_KEY sourcing and rotation.

The key used to live as a literal in settings.py, committed to a public
repository. It now comes from the environment and is mandatory in production,
so a deployment cannot quietly run on a published key.

The startup behaviour is exercised by importing the settings in a subprocess:
settings are read once per process, so DEBUG and SECRET_KEY cannot be
meaningfully varied with override_settings.
"""

import os
import re
import subprocess
import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.test import TestCase, override_settings

IMPORT_SETTINGS = "import django; django.setup()"
PRINT_FALLBACKS = (
    "import django; django.setup(); from django.conf import settings; print(settings.SECRET_KEY_FALLBACKS)"
)


def read_env_file(path):
    values = {}
    with open(path) as f:
        for line in f:
            match = re.match(r"\A([A-Za-z_0-9]+)=(.*)\Z", line.strip())
            if match:
                values[match.group(1)] = match.group(2)
    return values


def start_django(code=IMPORT_SETTINGS, **overrides):
    """Import the settings in a clean process, with production-style env vars.

    Anything passed as None is removed from the environment.
    """
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(settings.BASE_DIR),
        "DJANGO_SETTINGS_MODULE": "canvas_gamification.settings",
    }
    env.update(read_env_file(os.path.join(settings.BASE_DIR, "env", "test.env")))
    for key, value in overrides.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(settings.BASE_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


class SecretKeySourcingTest(TestCase):
    def test_production_refuses_to_start_without_a_secret_key(self):
        result = start_django(SECRET_KEY=None, DEBUG="false")
        self.assertNotEqual(result.returncode, 0, "settings imported without a SECRET_KEY")
        self.assertIn("SECRET_KEY", result.stderr)

    def test_production_starts_with_a_secret_key(self):
        result = start_django(SECRET_KEY="a-perfectly-fine-production-key", DEBUG="false")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_debug_falls_back_to_a_development_key(self):
        # Local work and `manage.py` one-liners must not require any setup.
        result = start_django(SECRET_KEY=None, DEBUG="true")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_the_committed_literal_is_gone(self):
        with open(os.path.join(settings.BASE_DIR, "canvas_gamification", "settings.py")) as f:
            source = f.read()
        self.assertNotIn("=cv^=w$b8iw4q5", source)

    def test_fallbacks_are_split_on_whitespace(self):
        result = start_django(
            code=PRINT_FALLBACKS,
            SECRET_KEY="current",
            SECRET_KEY_FALLBACKS="older newer",
            DEBUG="false",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "['older', 'newer']")

    def test_fallbacks_default_to_empty(self):
        result = start_django(code=PRINT_FALLBACKS, SECRET_KEY="current", SECRET_KEY_FALLBACKS=None, DEBUG="false")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "[]")


class SecretKeyRotationTest(TestCase):
    """The point of the fallbacks: rotating must not break live tokens."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="rotation@example.com",
            email="rotation@example.com",
            password="an-ordinary-password",
        )
        self.old_key = "the-old-secret-key"
        self.new_key = "the-new-secret-key"

    def make_token(self):
        with override_settings(SECRET_KEY=self.old_key, SECRET_KEY_FALLBACKS=[]):
            return PasswordResetTokenGenerator().make_token(self.user)

    def test_token_from_the_old_key_survives_rotation_with_a_fallback(self):
        token = self.make_token()
        with override_settings(SECRET_KEY=self.new_key, SECRET_KEY_FALLBACKS=[self.old_key]):
            self.assertTrue(PasswordResetTokenGenerator().check_token(self.user, token))

    def test_token_from_the_old_key_dies_once_the_fallback_is_removed(self):
        token = self.make_token()
        with override_settings(SECRET_KEY=self.new_key, SECRET_KEY_FALLBACKS=[]):
            self.assertFalse(PasswordResetTokenGenerator().check_token(self.user, token))

    def test_new_tokens_verify_under_the_new_key(self):
        with override_settings(SECRET_KEY=self.new_key, SECRET_KEY_FALLBACKS=[self.old_key]):
            token = PasswordResetTokenGenerator().make_token(self.user)
            self.assertTrue(PasswordResetTokenGenerator().check_token(self.user, token))
