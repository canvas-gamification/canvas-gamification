from django.contrib.auth import views as auth_views
from django.urls import path, re_path

from accounts.views import signup_view, activate, UserProfileView, PasswordChangeView, password_change_done_view, \
    forgot_password_view, password_reset_view, LoginView, consent_view

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', signup_view, name='signup'),
    path('profile/', UserProfileView.as_view(), name='profile'),

    path('change-password/', PasswordChangeView.as_view(), name="password_change"),
    path('password-change-done/', password_change_done_view, name="password_change_done"),
    re_path('activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
            activate, name='activate'),

    path('forgot-password/', forgot_password_view, name="password_forgot"),
    re_path('reset-password/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
            password_reset_view, name='password_reset'),

    path('consent/', consent_view, name='consent')
]
