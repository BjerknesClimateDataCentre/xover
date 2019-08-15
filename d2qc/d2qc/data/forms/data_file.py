from django.forms import ModelForm, FileInput
from d2qc.data.models import DataFile
from django.core.exceptions import ValidationError


class DataFileForm(ModelForm):
    class Meta:
        model = DataFile
        fields = ['filepath', 'name', 'description']
        widgets = {
            "filepath": FileInput(
                attrs={
                    'onchange':
                    """
                        var filename = '';
                        if (this.files.length > 0) {
                            filename = this.files[0].name;
                        }

                        document.getElementById('id_name').value = filename;
                    """
                })
        }
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(DataFileForm, self).__init__(*args, **kwargs)


    def clean_filepath(self):
        for chunk in self.cleaned_data['filepath'].chunks():
            try:
                chunk = chunk.decode('iso-8859-1')
            except:
                try:
                    chunk = chunk.decode('utf-8')
                except Exception as e:
                    raise ValidationError(
                        'Character encoding not in (utf-8, iso-8859-1)'
                    )
            break
        return self.cleaned_data['filepath']

    def clean_name(self):
        user_has_file = DataFile.objects.filter(
            name=self.cleaned_data['name'],
            owner=self.user,
        ).exists()
        if user_has_file:
            ok = False
            raise ValidationError(
                    "Name exists: '{}'. Try a different name.".format(
                        self.cleaned_data['name'],
                    ),
            )
        return self.cleaned_data['name']
