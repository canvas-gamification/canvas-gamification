from django.shortcuts import render
from django.http import HttpResponse
from .utils import init_analytics, init_question_metrics


def analysis(request):
    init_analytics.analytics()
    init_question_metrics.init()
    # init_event_metrics.init()
    return HttpResponse("ok", content_type='application/json')

