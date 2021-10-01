from django.shortcuts import render

# Create your views here.
from general.models.faq import FAQ


def faq(request):
    faqs = FAQ.objects.all()

    return render(request, 'faq.html', {
        'faqs': faqs,
        'header': 'faq',
    })
