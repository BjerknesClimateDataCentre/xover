from django.forms import ModelForm, RadioSelect
from d2qc.data.models import Profile

class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = [
            'min_depth',
            'crossover_radius',
            'depth_metric',
            'only_qc_controlled_data',
        ]
        widgets = {
            'depth_metric': RadioSelect(attrs={'cols': 80, 'rows': 20}),
        }
