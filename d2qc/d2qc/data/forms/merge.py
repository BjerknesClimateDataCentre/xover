from django import forms


class MergeForm(forms.Form):

    def __init__(self, *args, **kwargs):
        try:
            data_types = kwargs.pop('data_types')
        except KeyError:
            data_types = None
        super().__init__(*args, **kwargs)
        if data_types is not None:
            choices = [(t['id'], '') for t in data_types]
            self.fields['primary'] = forms.ChoiceField(
                label = "Pri.",
                widget = forms.RadioSelect,
                choices=choices
            )
            self.fields['secondary'] = forms.ChoiceField(
                label = "Sec.",
                widget = forms.RadioSelect,
                choices=choices
            )
