from d2qc.data.models import Profile, DataSet, DataValue, DataTypeName
from d2qc.data.models import Operation, OperationType
from django import forms
from django.conf import settings

import copy

class NormalizeForm(forms.Form):

    _params_opts = None

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('params_opts')
        data_set_id = int(kwargs.pop('data_set_id'))
        super().__init__(*args, **kwargs)
        self.fields['params'] = forms.MultipleChoiceField(
            label = "Select parameters to normalize",
            widget = forms.CheckboxSelectMultiple(
                choices = choices,
            ),
            choices = choices,
            required = False,
        )
        self._params_opts = dict(choices)
        self.fields['data_set_id'] = forms.IntegerField(
            widget=forms.HiddenInput,
            initial = data_set_id,
        )

    def save_normalization_data(self, data_set, user):
        output = []
        for parameter in self.cleaned_data['params']:
            operation = data_set.normalize_data(parameter, user)
            data_type_norm = DataTypeName.objects.get(
                pk=operation.data_type_name.id
            )
            data_type = DataTypeName.objects.get(
                pk=operation.data['original_parameter_id']
            )
            output.append({
                'name': data_type.name,
                'norm_name': data_type_norm.name,
            })

        return output
