from django import forms
from .models import FUBMessageUser

class FUBMessageUserAdminForm(forms.ModelForm):
    firstname = forms.CharField(max_length=100, required=False)
    lastname = forms.CharField(max_length=100, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = FUBMessageUser
        fields = '__all__'
