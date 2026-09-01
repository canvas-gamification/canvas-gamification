from drf_queryfields import QueryFieldsMixin
from rest_framework import serializers

from general.models.action import Action


class ActionsSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Action
        exclude = []
        # ``token_change`` is the token ledger; only server-side services may write it.
        read_only_fields = ["actor", "token_change", "time_created", "time_modified"]
