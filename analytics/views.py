from django.shortcuts import render
from django.http import HttpResponse
from .utils import init_analytics


def analysis(request):
    init_analytics.analytics()
    return HttpResponse("ok", content_type='application/json')

