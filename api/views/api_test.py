from rest_framework import viewsets


from course.models.models import TestModel
from api.serializers import TestSerializer

class ApiTestViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return TestModel.objects.all()
    serializer_class = TestSerializer