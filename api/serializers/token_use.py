from rest_framework import serializers

from api.serializers import TokenUseOptionSerializer
from canvas.models import TokenUse


class TokenUseSerializer(serializers.ModelSerializer):
    option = TokenUseOptionSerializer()

    class Meta:
        model = TokenUse
        fields = ['option', 'num_used']
