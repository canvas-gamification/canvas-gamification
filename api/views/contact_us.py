from rest_framework import mixins, viewsets

from api.serializers import ContactUsSerializer
from api.throttling import ConfigurableScopedRateThrottle


class ContactUsViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ContactUsSerializer
    throttle_classes = [ConfigurableScopedRateThrottle]
    throttle_scope = "contact-us"
