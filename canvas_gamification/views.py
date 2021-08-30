import mimetypes
import posixpath
from pathlib import Path

from django.http import (
    FileResponse, HttpResponseNotModified,
)
from django.shortcuts import render
from django.utils._os import safe_join
from django.utils.http import http_date
from django.views.static import was_modified_since

from course.models.models import UserQuestionJunction
from general.models.action import Action


def homepage(request):
    if request.user.is_authenticated:
        recently_viewed = request.user.question_junctions.order_by('-last_viewed')[:5]
        actions = request.user.actions.all()[:5]
    else:
        recently_viewed = UserQuestionJunction.objects.none()
        actions = Action.objects.none()

    return render(request, "homepage.html", {
        'header': 'homepage',
        'recently_viewed': recently_viewed,
        'actions': actions,
    })


def action_view(request):
    actions = request.user.actions.order_by("-time_modified").all()

    return render(request, 'actions.html', {
        'header': 'Actions',
        'actions': actions,
    })


def angular(request, path='index.html', document_root=None):
    path = posixpath.normpath(path).lstrip('/')
    fullpath = Path(safe_join(document_root, path))
    if not fullpath.exists():
        fullpath = Path(safe_join(document_root, 'index.html'))
    statobj = fullpath.stat()
    if not was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'),
                              statobj.st_mtime, statobj.st_size):
        return HttpResponseNotModified()
    content_type, encoding = mimetypes.guess_type(str(fullpath))
    content_type = content_type or 'application/octet-stream'
    response = FileResponse(fullpath.open('rb'), content_type=content_type)
    response["Last-Modified"] = http_date(statobj.st_mtime)
    if encoding:
        response["Content-Encoding"] = encoding
    return response
