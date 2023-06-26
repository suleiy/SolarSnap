# forms.py
from django import forms
from django.forms import ModelForm,TextInput,ImageField,FileInput

from .models import Image

class ImageForm(ModelForm):

    class Meta:
        model = Image
        fields = ['name','uploaded_image']
        widgets = {
            'name': TextInput(attrs={
                'class': "form-control",
                'style': 'max-width: 300px;',
                'placeholder': 'Input file name'
                }),
            'uploaded_image': FileInput(attrs={
                'style': 'max-width: 300px;',
                'placeholder': 'Upload Image'
                })
        }
