from django import forms
from d2qc.data.models import DataType, DataValue, Depth, DataSet
import pandas as pd

class MergeForm(forms.Form):
    merge_type = forms.ChoiceField(
        label = "Merge type action",
        choices=[
            (0, "0 - Do not merge"),
            (1, "1 - Merge using none"),
            (2, "2 - Merge using only secondary, no primary parameter"),
            (3, "3 - Merge using only primary, no secondary parameter"),
            (4, "4 - Merge using primary (few or no secondary or primary>80%)."),
            (5, "5 - Merge using mean of primary and UNCHANGED secondary."),
            (6, "6 - Merge using mean of primary and fitted secondary."),
            (7, "7 - Merge using primary because bad fit of secondary."),
        ],
        initial = '0',
    )

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

    def save_merge_data(self, data_set):
        primary = DataType.objects.get(pk=self.cleaned_data['primary'])
        secondary = DataType.objects.get(pk=self.cleaned_data['secondary'])
        name = "{}#{}_{}".format(
            self.cleaned_data['merge_type'],
            primary.original_label,
            secondary.original_label,
        )
        data = self.get_merge_data(data_set)
        data_type, found = DataType.objects.get_or_create(original_label=name)
        for i, d in enumerate(data['depth_id']):
            merge_type = int(self.cleaned_data['merge_type'])
            value = None
            if merge_type in [2,3,4,7]:
                name = 'secondary' if merge_type == 2 else 'primary'
                value = DataValue(
                    value = data[name][i],
                    qc_flag = 2,
                    data_type = data_type
                )
            else if merge_type == 5:
                arr = [ v for v in [
                    data['primary'][i],
                    data['secondary'][i],
                ] if v is not None]
                value = DataValue(
                    value = sum(arr)/len(arr),
                    qc_flag = 2,
                    data_type = data_type
                )


            if value is not None and value.value is not None:
                value.depth_id = d
                value.save()

        data_set.set_type_list(None)

    def get_merge_data(self, data_set):
        s1 = data_set.get_stations(
            parameter_id=self.cleaned_data['primary']
        )
        s2 = data_set.get_stations(
            parameter_id=self.cleaned_data['secondary']
        )
        stations = set(s1) and set(s2)

        primary = data_set.get_profiles_data(
            stations,
            self.cleaned_data['primary'],
            min_depth = 0,
        )
        secondary = data_set.get_profiles_data(
            stations,
            self.cleaned_data['secondary'],
            min_depth = 0,
        )
        merged = primary.merge(
            secondary[['depth_id','param']],
            how = 'inner',
            left_on = ['depth_id'],
            right_on = ['depth_id'],
            suffixes = ('_pri', '_sec'),
        )
        merged['diff'] = merged['param_pri'] - merged['param_sec']
        merged = merged.replace({pd.np.nan: None})
        result = {
            'depth': merged['depth'].tolist(),
            'diff': merged['diff'].tolist(),
            'depth_id': merged['depth_id'].tolist(),
            'primary': merged['param_pri'].tolist(),
            'secondary': merged['param_sec'].tolist(),
        }

        return result
