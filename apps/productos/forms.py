from django import forms
from .models import Resena

class ResenaForm(forms.ModelForm):
    class Meta:
        model = Resena
        fields = ['comentario', 'estrellas']