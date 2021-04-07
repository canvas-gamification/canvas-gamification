from rest_framework import serializers

from api.serializers import UpdateListSerializer
from course.models.models import TokenValue


class TokenValueSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance.value = validated_data.get('value', instance.value)
        instance.save()
        return instance

    class Meta:
        model = TokenValue
        fields = ['value', 'category', 'difficulty', 'pk']
        list_serializer_class = UpdateListSerializer
