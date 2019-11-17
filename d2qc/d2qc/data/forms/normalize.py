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
            intercept = DataSet.get_norm_regression_intercept(
                parameter,
                area_polygon = settings.ARCTIC_REGION
            )
            profile = data_set.get_profiles_data(
                stations = data_set.get_stations(
                    parameter_id = parameter,
                    crossover_radius = user.profile.crossover_radius,
                    min_depth = user.profile.min_depth,
                    only_qc_controlled_data = (
                        user.profile.only_qc_controlled_data
                    ),
                ),
                parameter_id = parameter,
                min_depth = user.profile.min_depth,
                only_qc_controlled_data = user.profile.only_qc_controlled_data,
            )
            # Calculate mean of available salinity values in stations with
            salm = profile['salin'].mean()
            # Remove rows with missing values
            profile.dropna(
                inplace =True,
                subset = ['param', 'salin']
            )
            # Calculate normalized values
            profile['param_norm']=(
                (
                    (profile['param'] - intercept)
                    / profile['salin']
                    * salm
                )
                + intercept
            )
            data_type = DataTypeName.objects.get(pk = parameter)
            norm_name = "NORM#{}".format(data_type.name)
            data_type_norm = DataTypeName.objects.filter(name=norm_name)
            operation_type = OperationType.objects.filter(
                name='normalization'
            ).first()
            if data_type_norm.exists():
                data_type_norm = data_type_norm.first()
            else:
                data_type_norm = copy.copy(data_type)
                data_type_norm.id = None
                data_type_norm.name = norm_name
                data_type_norm.operation_type = operation_type
                data_type_norm.save()

            value_list = []
            for index, row in profile.iterrows():
                value = DataValue(qc_flag=2, data_type_name = data_type_norm)
                value.depth_id = row['depth_id']
                value.value = row['param_norm']
                value_list.append(value)

            DataValue.objects.bulk_create(value_list)

            # Update operations table if successful
            operation = Operation(
                operation_type = operation_type,
                data_type_name = data_type_norm,
                data_set = data_set,
                name = (
                    f"{data_type.name} to {data_type_norm.name}"
                ),
                data = {
                    'orig_parameter_id': data_type.id,
                    'norm_parameter_id': data_type_norm.id,
                    'salinity_mean': salm,
                    'min_depth': user.profile.min_depth,
                    'only_qc_controlled_data': (
                        user.profile.only_qc_controlled_data
                    ),
                }
            )
            operation.save()
            output.append({
                'name': data_type.name,
                'norm_name': data_type_norm.name,
            })

        return output
