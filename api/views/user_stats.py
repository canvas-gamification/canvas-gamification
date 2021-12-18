from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from accounts.models import MyUser
from api.serializers import UserStatsSerializer


class UserStatsViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return MyUser.objects.filter(id=self.request.user.id)
    serializer_class = UserStatsSerializer
    permission_classes = [IsAuthenticated, ]

    @action(detail=False, methods=['get'], url_path='difficulty/(?P<category_pk>[^/.]+)')
    def difficulty(self, request, category_pk=None):
        user_stats = []
        for stats in request.user.success_rate_by_difficulty:
            if stats['category'] == int(category_pk):
                user_stats.append(stats)
        return Response(user_stats, status=status.HTTP_200_OK)
