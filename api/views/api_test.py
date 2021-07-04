from rest_framework import viewsets


from course.models.models import TestModel
from accounts.models import MyUser
from api.serializers import TestSerializer

class ApiTestViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # return MyUser.objects.all() #Use with actual users in database

        return TestModel.objects.all()
    serializer_class = TestSerializer