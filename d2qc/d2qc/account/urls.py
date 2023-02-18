from django.contrib import admin
from django.contrib.auth.views import LogoutView, PasswordResetView
from django.urls import include, path
from d2qc.account.views import SignUp, UpdateUser, Login


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path(
        'login',
        Login.as_view(template_name='registration/login.html'),
        name='account-login'
    ),
    path(
        'login/activated',
        Login.as_view(template_name='registration/login.html'),
        name='account-login-activated'
    ),
    path(
        'login/activate/<slug:uid>/<slug:token>/',
        Login.as_view(template_name='registration/login.html'),
        name='account-login-activate'
    ),
    path(
        'logout',
        LogoutView.as_view(),
        name='account-logout'
    ),
    path(
        'password_reset',
        PasswordResetView.as_view(template_name='registration/reset.html'),
        name='account-reset'
    ),
    path(
        'update/<int:pk>',
        UpdateUser.as_view(),
        name='account-update'
    ),
    path('signup', SignUp.as_view(), name='account-signup'),
]
