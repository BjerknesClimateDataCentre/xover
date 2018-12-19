from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from d2qc.account.forms import SignupForm
from d2qc.account.tokens import account_activation_token
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.views.generic import CreateView
from django.views.generic import UpdateView
from django.core.mail import EmailMessage
from django.conf import settings

class SignUp(CreateView):
    form_class = SignupForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.is_active = False
        self.object.save()
        if settings.EMAIL_HOST: # Email is set up
            current_site = get_current_site(self.request)
            mail_subject = 'Activate account for GLODAP Crossover'
            message = render_to_string('registration/activation_email.html', {
                'user': self.object,
                'domain': current_site.domain,
                'uid': self.object.pk,
                'token': account_activation_token.make_token(self.object),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            messages.success(
                self.request,
                "Confirm your email to complete the registration."
            )
        return super().form_valid(form)

class UpdateUser(UpdateView):
    model = User
    fields = (
            'first_name',
            'last_name',
            'email',
    )
    template_name = 'registration/update.html'
    success_url = reverse_lazy('data')
    def form_valid(self, form):
        self.object = form.save(commit=False)
        messages.success(
            self.request,
            "Updated user {}.".format(self.object.first_name)
        )
        return super().form_valid(form)

class Login(LoginView):
    def get_context_data(self, **kwargs):
        try:
            user = User.objects.get(pk=self.kwargs.get('uid'))
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        token = self.kwargs.get('token')
        if (
                user is not None and
                account_activation_token.check_token(user, token)
        ):
            user.is_active = True
            user.save()
            messages.success(
                    self.request,
                    'Account activated, log in to continue'
            )
        elif token:
            messages.error(
                    self.request,
                    'Activation link is invalid'
            )
        return super().get_context_data(**kwargs)
