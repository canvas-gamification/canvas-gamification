from rest_framework import viewsets
from canvas.models import CanvasCourse
from api.serializers import CourseNamesSerializer


class CourseNamesViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return CanvasCourse.objects.all()

    serializer_class = CourseNamesSerializer
