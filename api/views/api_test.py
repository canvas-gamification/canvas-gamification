from rest_framework import viewsets
from rest_framework.response import Response

class ApiTestViewSet(viewsets.ViewSet):

    def list(self, request):
        res = [
            {
                'user': 'user1',
                'tokens': 5,
            },
            {
                'user': 'user2',
                'tokens': 7,
            },
            {
                'user': 'user3',
                'tokens': 2
            },
        ]
        return Response(res)