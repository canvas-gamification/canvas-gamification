from rest_framework import serializers

from canvas.models import CanvasCourse


class CourseSerializer(serializers.ModelSerializer):
    is_registered = serializers.SerializerMethodField('get_is_registered')

    def get_is_registered(self, course):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user

        # if user is not logged in or the request has no user attached
        if user is None or not user.is_authenticated:
            return False

        return course.is_registered(user)

    class Meta:
        model = CanvasCourse
        fields = ['id', 'mock', 'name', 'url', 'course_id', 'token', 'allow_registration', 'visible_to_students',
                  'start_date', 'end_date', 'instructor', 'status', 'is_registered']
