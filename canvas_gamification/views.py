from django.shortcuts import render


# Create your views here.
from course.models.models import UserQuestionJunction
from general.models import Action


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
