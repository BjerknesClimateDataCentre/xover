from d2qc.data.models import Profile

from django.views.generic.edit import UpdateView
from django.contrib import messages

class ProfileUpdate(UpdateView):
    model = Profile
    fields = ['min_depth','crossover_radius']
    def get_success_url(self):
        return reverse('data')
    def get_object(self):
        try:
            return self.request.user.profile
        except:
            self.request.user.profile = Profile(user=self.request.user)
            self.request.user.save()
        return self.request.user.profile

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(
            self.request,
            "Profile settings updated"
        )
        return super().form_valid(form)
