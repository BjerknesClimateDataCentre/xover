from django import forms


class MergeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        params = []
        if 'params' in kwargs:
            params = kwargs.pop('params')
        super().__init__(kwargs)
        self.fields = {}

        choices = []
        for param in params:
            choices.append((param['id'], ""))
        self.fields = {
            "primary": forms.ChoiceField(
                label = "Pri.",
                choices = choices,
                widget = forms.RadioSelect,
            ),
            "secondary": forms.ChoiceField(
                label = "Sec.",
                choices = choices,
                widget = forms.RadioSelect,
            ),
        }
