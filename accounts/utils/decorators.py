from functools import wraps

from django.contrib import messages


def show_login(message):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapper_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                request.show_login = True
                messages.add_message(request, messages.ERROR, message)
            return view_func(request, *args, **kwargs)

        return _wrapper_view

    return decorator
