from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.urls import include, path
from django.conf.urls import url
from d2qc.account.views import SignUp


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path(
        'login',
        LoginView.as_view(template_name='registration/login.html')
    ),
    path(
        'logout',
        LogoutView.as_view()
    ),
    path(
        'password_reset',
        PasswordResetView.as_view(template_name='registration/reset.html')
    ),
    path('signup', SignUp.as_view(), name='signup'),
]
