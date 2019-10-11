from django import forms
from django.core.cache import cache

class CalculationOptionsForm(forms.Form):
    depth_metric = forms.ChoiceField(
        label = "Choose depth metric",
        widget = forms.RadioSelect,
        initial = 'sigma4',
        choices = [
            ('sigma4', "Sigma 4"),
            ('depth', "Pressure (dbar)"),
        ]
    )
    only_qc_controlled_data = forms.BooleanField(
        label = "Only show QC controlled data",
        initial = False,
        required = False,
    )

    def __init__(self, *args, user_id=0, **kwargs):
        self.user_id = user_id
        super().__init__(*args, **kwargs)

    def is_valid(self):
        retval = super().is_valid()
        # Update cache after validating
        if retval:
            cache.set(
                f"calculation_options_{self.user_id}",
                self.cleaned_data
            )
        return retval
