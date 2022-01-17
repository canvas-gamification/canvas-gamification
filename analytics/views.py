from django.http import HttpResponse

from analytics.utils import init_analytics


def analysis(request):
    init_analytics.init()
    return HttpResponse("ok", content_type='application/json')
