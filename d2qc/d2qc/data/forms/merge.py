from django import forms
from d2qc.data.models import DataType, DataValue, Depth, DataSet
import pandas as pd
import numpy as np
import copy

class MergeForm(forms.Form):
    merge_type = forms.ChoiceField(
        label = "Merge type action",
        choices=[
            (1, "1 - Do not merge"),
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
        data = data_set.get_merge_data(
            self.cleaned_data['primary'],
            self.cleaned_data['secondary'],
        )

        if DataType.objects.filter(original_label=name).exists():
            data_type = DataType.objects.filter(original_label=name).first()
        else:
            data_type = copy.copy(primary)
            data_type.id = None
            data_type.original_label = name
            data_type.save()

        merge_type = int(self.cleaned_data['merge_type'])
        if merge_type == 6:
            data.dropna(subset=['primary', 'secondary'], inplace=True)
            slope, intercept = np.polyfit(
                data['primary'],
                data['secondary'],
                1
            )
            data['secondary'] = (data['secondary'] - intercept) / slope

        for i, row in data.iterrows():
            value = DataValue(qc_flag=2,data_type=data_type)
            value.depth_id = row['depth_id']
            value.value = np.nan
            if merge_type in [2, 3, 4, 7]:
                name = 'secondary' if merge_type == 2 else 'primary'
                value.value = row[name]
            elif merge_type in [5, 6]:
                value.value = np.nanmean([row['primary'], row['secondary']])

            if not np.isnan(value.value):
                value.save()

        data_set.set_type_list(None)
