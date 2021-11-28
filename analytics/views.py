from django.shortcuts import render
from django.http import HttpResponse
from .utils import get_submission


def analysis(request):
    get_submission.submission_analytics()
    return HttpResponse("ok", content_type='application/json')

