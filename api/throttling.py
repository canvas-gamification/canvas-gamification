from django.conf import settings
from rest_framework.throttling import ScopedRateThrottle


class ConfigurableScopedRateThrottle(ScopedRateThrottle):
    """
    ScopedRateThrottle that can be switched off with ``API_THROTTLING_ENABLED=false``
    (the test suite logs in far more often per minute than any real client).
    """

    def allow_request(self, request, view):
        if not getattr(settings, "API_THROTTLING_ENABLED", True):
            return True
        return super().allow_request(request, view)
