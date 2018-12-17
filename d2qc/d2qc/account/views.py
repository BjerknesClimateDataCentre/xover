from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from d2qc.account.forms import SignupForm
from d2qc.account.tokens import account_activation_token
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.views.generic import CreateView
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

def activate(request, uid, token):
    try:
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        # return redirect('home')
        messages.success(
            request,
            "Confirm your email to complete the registration."
        )
        return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        return HttpResponse('Activation link is invalid!')
