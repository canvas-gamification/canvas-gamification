from rest_framework import mixins, viewsets

from api.serializers import ContactUsSerializer


class ContactUsViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ContactUsSerializer
