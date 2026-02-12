from django import forms


class UploadExcelForm(forms.Form):
    """Form per upload file Excel"""

    file = forms.FileField(
        label='File Excel',
        help_text='Carica un file .xlsx con la lista materiale',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Verifica estensione
            ext = file.name.split('.')[-1].lower()
            if ext not in ['xlsx', 'xls']:
                raise forms.ValidationError('Il file deve essere un file Excel (.xlsx o .xls)')
        return file
