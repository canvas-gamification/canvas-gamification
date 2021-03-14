import django_property_filter

from course.models.models import Question


class QuestionFilterSet(django_property_filter.PropertyFilterSet):

    class Meta:
        model = Question
        fields = ['author', 'difficulty', 'course', 'event', 'is_verified', 'is_sample']
        property_fields = [
            ('parent_category_name', django_property_filter.PropertyCharFilter, ['exact']),
        ]
