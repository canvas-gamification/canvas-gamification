"""Serving of the built Angular bundle by canvas_gamification.views.angular.

These run against the production URLconf: urls.py branches on settings.DEBUG at
import time, and Django's test runner forces DEBUG off, so the catch-all that
serves static/angular is the one under test here (the DEBUG URLconf does not
mount it at all).

Nothing else in the suite requests a non-API path, which is how the Django 4.1
signature change to was_modified_since() -- it lost its third "size" argument --
reached master and turned every page and asset in a DEBUG=false deployment into
a 500.
"""

import os

from django.conf import settings
from django.test import TestCase
from django.utils.http import http_date

ANGULAR_ROOT = os.path.join(settings.BASE_DIR, "static", "angular")


def read_response(response):
    if response.streaming:
        return b"".join(response.streaming_content)
    return response.content


def find_bundle():
    """Any hashed .js bundle at the root of the build output.

    Discovered rather than hard-coded: the file names carry content hashes and
    change on every frontend build.
    """
    for name in sorted(os.listdir(ANGULAR_ROOT)):
        if name.endswith(".js"):
            return name
    return None


class AngularServingTest(TestCase):
    def test_root_serves_index_html(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html")
        self.assertIn(b"<app-root", read_response(response))

    def test_root_sets_last_modified(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header("Last-Modified"))

    def test_hashed_bundle_is_served_with_its_own_content_type(self):
        bundle = find_bundle()
        self.assertIsNotNone(bundle, "no .js bundle in static/angular -- has the frontend been built?")

        response = self.client.get("/" + bundle)
        self.assertEqual(response.status_code, 200)
        # Serves the real file, not the index.html fallback.
        self.assertIn("javascript", response["Content-Type"])
        with open(os.path.join(ANGULAR_ROOT, bundle), "rb") as f:
            self.assertEqual(read_response(response), f.read())

    def test_unknown_path_falls_back_to_index_html(self):
        # Client-side routes must reach the Angular app rather than 404.
        response = self.client.get("/some/client/side/route")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html")
        with open(os.path.join(ANGULAR_ROOT, "index.html"), "rb") as f:
            self.assertEqual(read_response(response), f.read())

    def test_if_modified_since_in_the_future_returns_304(self):
        # The direct regression test for the was_modified_since() signature:
        # this is the only branch that calls it with a header present.
        response = self.client.get("/", HTTP_IF_MODIFIED_SINCE=http_date(2**31 - 1))
        self.assertEqual(response.status_code, 304)

    def test_if_modified_since_in_the_past_returns_the_file(self):
        response = self.client.get("/", HTTP_IF_MODIFIED_SINCE=http_date(0))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<app-root", read_response(response))

    def test_api_routes_are_not_swallowed_by_the_catch_all(self):
        # The catch-all is registered last; /api/ must still reach the API.
        response = self.client.get("/api/course/")
        self.assertIn(response.status_code, [401, 403])
