from django import forms
from d2qc.data.models import DataTypeName, DataValue, Depth, DataSet
from d2qc.data.models import Operation, OperationType
import pandas as pd
import numpy as np
import glodap.util.stats as stats
import copy
from django.core.cache import cache

class MergeForm(forms.Form):
    _cache_name = "merge_form"
    INITIAL_MERGE_TYPE = 1
    INITIAL_MERGE_MIN_DEPTH = 0
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
        initial = INITIAL_MERGE_TYPE,
    )
    merge_min_depth = forms.IntegerField(
        initial = INITIAL_MERGE_MIN_DEPTH,
        min_value = 0,
        required = True,
        label = "Minimum depth used to calculate linear fit",
        widget = forms.TextInput,
    )

    def __init__(self, *args, **kwargs):
        try:
            data_type_names = kwargs.pop('data_type_names')
        except KeyError:
            data_type_names = None

        if data_type_names:
            primary = int(cache.get(f"{self._cache_name}__primary"))
            secondary = int(cache.get(f"{self._cache_name}__secondary"))
            merge_min_depth = cache.get(
                f"{self._cache_name}__merge_min_depth",
                self.INITIAL_MERGE_MIN_DEPTH,
            )
            merge_type = cache.get(
                f"{self._cache_name}__merge_type",
                self.INITIAL_MERGE_TYPE,
            )
            # Only use cache data if data types exists in data_type_names
            if (
                    MergeForm.in_data_type_names(
                        primary,
                        secondary,
                        data_type_names,
                    )
            ):
                if len(args) == 0 and not 'data' in kwargs:
                    data = {
                        'primary': primary,
                        'secondary': secondary,
                        'merge_min_depth': merge_min_depth,
                        'merge_type': merge_type,
                    }
                    kwargs['data'] = data
            else:
                primary = None
                secondary = None

            choices = [(t['id'], '') for t in data_type_names]
            primary_field = forms.ChoiceField(
                label = "Pri.",
                widget = forms.RadioSelect,
                choices = choices,
                initial = primary,
            )
            secondary_field = forms.ChoiceField(
                label = "Sec.",
                widget = forms.RadioSelect,
                choices=choices,
                initial = secondary,
            )
        super().__init__(*args, **kwargs)
        self.fields['primary'] = primary_field
        self.fields['secondary'] = secondary_field

    @staticmethod
    def in_data_type_names(primary:int,secondary:int,data_type_names:list=[]):
        """
        return true if primary and secondary are found both found in
        data_type_names id. data_type_names is an array of dicts with an
        id property: data_type_names=[{'id':1},{'id':2},...]
        """
        p = 0
        s = 0
        for d in data_type_names:
            if int(d['id']) == int(primary):
                p = 1
            if int(d['id']) == int(secondary):
                s = 1
        return s + p == 2

    def is_valid(self):
        retval = super().is_valid()
        if retval:
            cache.set(
                f"{self._cache_name}__primary",
                self.cleaned_data['primary']
            )
            cache.set(
                f"{self._cache_name}__secondary",
                self.cleaned_data['secondary']
            )
            cache.set(
                f"{self._cache_name}__merge_min_depth",
                self.cleaned_data['merge_min_depth']
            )
            cache.set(
                f"{self._cache_name}__merge_type",
                self.cleaned_data['merge_type']
            )
        return retval

    def save_merge_data(self, data_set):
        primary = DataTypeName.objects.get(pk=self.cleaned_data['primary'])
        secondary = DataTypeName.objects.get(pk=self.cleaned_data['secondary'])
        name = "{}#{}_{}".format(
            self.cleaned_data['merge_type'],
            primary.name,
            secondary.name,
        )
        data = data_set.get_merge_data(
            self.cleaned_data['primary'],
            self.cleaned_data['secondary'],
            min_depth = self.cleaned_data['merge_min_depth'],
        )

        if DataTypeName.objects.filter(name=name).exists():
            data_type_name = DataTypeName.objects.filter(name=name).first()
        else:
            data_type_name = copy.copy(primary)
            data_type_name.id = None
            data_type_name.name = name
            data_type_name.save()

        merge_type = int(self.cleaned_data['merge_type'])
        slope, intercept = stats.linear_fit(
            data['primary'].tolist(),
            data['secondary'].tolist(),
        )
        if merge_type == 6:
            data['secondary'] = (data['secondary'] - intercept) / slope

        for i, row in data.iterrows():
            value = DataValue(qc_flag=2,data_type_name=data_type_name)
            value.depth_id = row['depth_id']
            value.value = np.nan
            if merge_type in [2, 3, 4, 7]:
                name = 'secondary' if merge_type == 2 else 'primary'
                value.value = row[name]
            elif merge_type in [5, 6]:
                value.value = np.nanmean([row['primary'], row['secondary']])

            if not np.isnan(value.value):
                value.save()

        # Update operations table if successful
        operation_type = OperationType.objects.filter(name='merge').first()
        operation = Operation(
            operation_type = operation_type,
            data_type_name = data_type_name,
            data_set = data_set,
            name = f"{primary.name} vs {secondary.name}, type #{merge_type}",
            data = {
                'merge_type': merge_type,
                'primary': {
                    'name': primary.name,
                    'id': primary.id,
                },
                'secondary': {
                    'name': secondary.name,
                    'id': secondary.id,
                },
            }
        )
        operation.save()
        data_set.set_type_list(None)
