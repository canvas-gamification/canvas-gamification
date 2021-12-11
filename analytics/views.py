from django.http import HttpResponse

from analytics.utils import init_question_analytics, init_analytics


def question_analytics(request):
    init_question_analytics.init()
    return HttpResponse("ok", content_type='application/json')


def submission_analytics(request):
    init_analytics.init_submission_analytics()
    return HttpResponse("ok", content_type='application/json')
