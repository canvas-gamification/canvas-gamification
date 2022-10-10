import mimetypes
import posixpath
from pathlib import Path

from django.http import (
    FileResponse,
    HttpResponseNotModified,
)
from django.utils._os import safe_join
from django.utils.http import http_date
from django.views.static import was_modified_since


def angular(request, path="index.html", document_root=None):
    path = posixpath.normpath(path).lstrip("/")
    fullpath = Path(safe_join(document_root, path))
    if not fullpath.exists():
        fullpath = Path(safe_join(document_root, "index.html"))
    statobj = fullpath.stat()
    if not was_modified_since(
        request.META.get("HTTP_IF_MODIFIED_SINCE"),
        statobj.st_mtime,
        statobj.st_size,
    ):
        return HttpResponseNotModified()
    content_type, encoding = mimetypes.guess_type(str(fullpath))
    content_type = content_type or "application/octet-stream"
    response = FileResponse(fullpath.open("rb"), content_type=content_type)
    response["Last-Modified"] = http_date(statobj.st_mtime)
    if encoding:
        response["Content-Encoding"] = encoding
    return response
