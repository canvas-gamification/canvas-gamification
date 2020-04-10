from django.shortcuts import redirect

from accounts.forms import LoginForm
from django.contrib.auth import login


def login_overlay_middleware(get_response):
    # One-time configuration and initialization.

    def middleware(request):
        if request.method == "POST" and request.POST.get('is_login', False):
            login_form = LoginForm(request, data=request.POST)
            if login_form.is_valid():
                login(request, login_form.get_user())
                return redirect(request.path)
            else:
                request.show_login = True
        else:
            login_form = LoginForm(request)
        request.login_form = login_form

        response = get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    return middleware
