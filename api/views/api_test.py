from rest_framework import viewsets


from course.models.models import TestModel
from accounts.models import MyUser
from course.models.models import TestModel
from api.serializers import TestSerializer

class ApiTestViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # return MyUser.objects.all() #Use with actual users in database
        return TestModel.objects.all()
        
<<<<<<< HEAD
        #comment
=======
        
>>>>>>> fbccc132012d5eb31b8d55af1e0be7af3268a2b8
    serializer_class = TestSerializer