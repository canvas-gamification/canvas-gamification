from rest_framework import serializers


class UpdateListSerializer(serializers.ListSerializer):
    # Can use this for any future serializers that need to be updated in batches

    def update(self, instances, validated_data):
        instance_hash = {index: instance for index, instance in enumerate(instances)}

        result = [
            self.child.update(instance_hash[index], attrs)
            for index, attrs in enumerate(validated_data)
        ]
        return result
