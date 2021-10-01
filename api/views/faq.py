from rest_framework import viewsets

from api.serializers import FAQSerializer
from general.models.faq import FAQ


class FAQViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
