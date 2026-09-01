from rest_framework import serializers


class UpdateListSerializer(serializers.ListSerializer):
    # Can use this for any future serializers that need to be updated in batches

    def update(self, instances, validated_data):
        instance_hash = {index: instance for index, instance in enumerate(instances)}

        result = [self.child.update(instance_hash[index], attrs) for index, attrs in enumerate(validated_data)]
        return result


class HideAnswerMixin:
    """
    Strip the model answer from a question payload unless the requesting user may
    edit the question. Serializers used without a request (internal callers) are
    left alone. Set ``hide_answer = False`` on a subclass to opt out.
    """

    hide_answer = True
    hidden_answer_fields = ("answer",)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not self.hide_answer:
            return data
        request = self.context.get("request", None)
        if request is None:
            return data
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated or not instance.has_edit_permission(user):
            for field in self.hidden_answer_fields:
                data.pop(field, None)
        return data
