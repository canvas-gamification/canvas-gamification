from rest_framework import serializers

from canvas.models import TokenUseOption


class TokenUseOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = TokenUseOption
        fields = ['course',
                  'tokens_required',
                  'points_given',
                  'maximum_number_of_use',
                  'assignment_name',
                  'assignment_id']
