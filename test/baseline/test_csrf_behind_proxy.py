"""CSRF and forwarded-scheme handling behind the reverse proxy.

Django 4.0 added strict Origin checking to CsrfViewMiddleware. The expected
origin is derived from request.is_secure(), so with TLS terminated upstream and
the forwarded scheme ignored, Django compares "http://host" against the
browser's "https://host" and rejects every unsafe-method request from a
session-authenticated page -- in practice, admin login.

The API is unaffected (token and basic auth, which are CSRF-exempt), which is
why nothing else in the suite covers this.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase, override_settings

from canvas_gamification.csrf import trusted_origins


class TrustedOriginsTest(TestCase):
    def test_builds_https_origins(self):
        self.assertEqual(trusted_origins(["example.com"]), ["https://example.com"])

    def test_skips_the_wildcard_host(self):
        # "*" is a valid ALLOWED_HOSTS entry but not a valid origin.
        self.assertEqual(trusted_origins(["*"]), [])

    def test_leading_dot_becomes_a_wildcard_origin(self):
        self.assertEqual(trusted_origins([".example.com"]), ["https://*.example.com"])

    def test_multiple_hosts_keep_their_order(self):
        self.assertEqual(
            trusted_origins(["a.example.com", "*", "b.example.com"]),
            ["https://a.example.com", "https://b.example.com"],
        )

    def test_empty_allowed_hosts(self):
        self.assertEqual(trusted_origins([]), [])

    def test_every_configured_origin_is_https_and_well_formed(self):
        # Not compared against ALLOWED_HOSTS directly: the test runner appends
        # "testserver" to it at runtime, after settings were imported.
        for origin in settings.CSRF_TRUSTED_ORIGINS:
            self.assertTrue(origin.startswith("https://"), origin)
            self.assertNotEqual(origin, "https://*")


class ForwardedSchemeTest(TestCase):
    def test_secure_proxy_ssl_header_is_configured(self):
        self.assertEqual(settings.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https"))

    def test_request_is_secure_when_the_proxy_forwards_https(self):
        request = RequestFactory().get("/", HTTP_X_FORWARDED_PROTO="https")
        self.assertTrue(request.is_secure())

    def test_request_is_not_secure_without_the_header(self):
        self.assertFalse(RequestFactory().get("/").is_secure())

    def test_request_is_not_secure_when_the_proxy_forwards_http(self):
        request = RequestFactory().get("/", HTTP_X_FORWARDED_PROTO="http")
        self.assertFalse(request.is_secure())


class AdminLoginOriginTest(TestCase):
    """The actual regression: a CSRF-enforcing POST to the admin login form."""

    def setUp(self):
        self.password = "sup3r-s3cret-pw"
        get_user_model().objects.create_superuser(
            username="csrf-admin",
            email="csrf-admin@example.com",
            password=self.password,
        )
        self.client = Client(enforce_csrf_checks=True)

    def post_login(self, **extra):
        # A real browser round trip: fetch the form for its CSRF cookie, then
        # post the matching token back.
        #
        # HTTP_HOST is set explicitly because the test client's environ carries
        # SERVER_PORT=80; once a request counts as HTTPS, get_host() would
        # append that port and produce "testserver:80". Nginx forwards the
        # real Host header (proxy_set_header HOST $host), so this matches
        # production rather than working around it.
        extra.setdefault("HTTP_HOST", "testserver")
        self.client.get("/admin/login/")
        token = self.client.cookies["csrftoken"].value
        return self.client.post(
            "/admin/login/",
            {
                "username": "csrf-admin",
                "password": self.password,
                "csrfmiddlewaretoken": token,
                "next": "/admin/",
            },
            **extra,
        )

    def test_https_origin_is_accepted_when_the_proxy_forwards_https(self):
        # The regression case: this is what a browser sends to the admin login
        # form through the TLS-terminating proxy.
        response = self.post_login(
            HTTP_ORIGIN="https://testserver",
            HTTP_X_FORWARDED_PROTO="https",
        )
        self.assertEqual(response.status_code, 302)

    def test_https_origin_is_rejected_without_the_forwarded_scheme(self):
        # Pins the pre-fix behaviour: this is exactly what a TLS-terminating
        # proxy produced before SECURE_PROXY_SSL_HEADER was set.
        response = self.post_login(HTTP_ORIGIN="https://testserver")
        self.assertEqual(response.status_code, 403)

    def test_foreign_origin_is_still_rejected(self):
        response = self.post_login(
            HTTP_ORIGIN="https://evil.example.com",
            HTTP_X_FORWARDED_PROTO="https",
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(ALLOWED_HOSTS=["testserver"], CSRF_TRUSTED_ORIGINS=["https://testserver"])
    def test_trusted_origin_is_accepted_even_without_the_forwarded_scheme(self):
        # The second, independent mechanism: CSRF_TRUSTED_ORIGINS is consulted
        # regardless of is_secure(), so a deployment whose proxy does not send
        # X-Forwarded-Proto is still covered.
        response = self.post_login(HTTP_ORIGIN="https://testserver")
        self.assertEqual(response.status_code, 302)

    def test_same_origin_http_still_works(self):
        # A plain-http deployment needs no trusted origin at all.
        response = self.post_login(HTTP_ORIGIN="http://testserver")
        self.assertEqual(response.status_code, 302)
