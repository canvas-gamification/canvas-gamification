from drf_queryfields import QueryFieldsMixin
from rest_framework import serializers

from general.models.page_view import PageView


class PageViewSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = PageView
        exclude = []
        read_only_fields = ["user"]
