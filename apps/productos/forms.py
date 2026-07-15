from django import forms
from .models import Resena

class ResenaForm(forms.ModelForm):
    estrellas = forms.TypedChoiceField(
        choices=[(value, f'{value} estrella' if value == 1 else f'{value} estrellas') for value in range(1, 6)],
        coerce=int,
    )
    class Meta:
        model = Resena
        fields = ['comentario', 'estrellas']
