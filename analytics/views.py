from django.http import HttpResponse


def analysis(request):
    return HttpResponse("ok", content_type='application/json')
