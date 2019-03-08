from django.forms import ModelForm, FileInput
from d2qc.data.models import DataFile


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

    def clean_filepath(self):
        for chunk in self.cleaned_data['filepath'].chunks():
            try:
                chunk = chunk.decode('iso-8859-1')
            except:
                try:
                    chunk = chunk.decode('utf-8')
                except Exception as e:
                    raise ValidationError(
                        _('Character encoding not in (utf-8, iso-8859-1)')
                    )
            break
        return self.cleaned_data['filepath']
