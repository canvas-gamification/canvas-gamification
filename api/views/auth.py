from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from general.services.action import create_login_action


class ObtainAuthTokenView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        create_login_action(user)
        return Response({
            'id': user.id,
            'token': token.key,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'tokens': user.tokens,
            'role': user.role,
            'is_teacher': user.is_teacher,
            'is_student': user.is_student,
            'has_consent': user.has_consent,
        })
