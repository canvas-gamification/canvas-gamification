import re

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from canvas.models import CanvasCourse
from canvas.utils.token_use import update_token_use, TokenUseException


# TODO: get course_pk from url query param
@api_view(['POST'])
def use_tokens(request, course_pk):
    course = get_object_or_404(CanvasCourse, pk=course_pk)
    token_use_data = {}
    for key in request.data.keys():
        match = re.fullmatch(r"token_use#(\d+)", key)
        if match:
            token_use_option_id = int(match.group(1))
            token_use_num = int(request.data.get(key, '0') or 0)
            token_use_data[token_use_option_id] = token_use_num
    try:
        update_token_use(request.user, course, token_use_data)
        return Response({
            "message": {
                "type": "SUCCESS",
                "content": "Tokens Updated Successfully"
            }
        })
    except TokenUseException:
        return Response({
            "message": {
                "type": "ERROR",
                "content": "Invalid Use of Tokens"
            }
        }, status=status.HTTP_400_BAD_REQUEST)
