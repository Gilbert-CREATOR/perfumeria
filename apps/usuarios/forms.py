from django import forms
from .models import PerfilUsuario, Direccion

class PerfilForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['telefono', 'fecha_nacimiento']
        widgets = {
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (809) 123-4567'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }

class DireccionForm(forms.ModelForm):
    class Meta:
        model = Direccion
        fields = [
            'tipo', 'nombre_completo', 'telefono', 'direccion',
            'ciudad', 'provincia', 'codigo_postal', 'pais', 'es_predeterminada'
        ]
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'nombre_completo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Juan Pérez'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (809) 123-4567'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Calle Principal #123, Apt 4A'
            }),
            'ciudad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Santo Domingo'
            }),
            'provincia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Distrito Nacional'
            }),
            'codigo_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10101'
            }),
            'pais': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'República Dominicana'
            }),
            'es_predeterminada': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre_completo'].label = 'Nombre Completo'
        self.fields['telefono'].label = 'Teléfono'
        self.fields['direccion'].label = 'Dirección'
        self.fields['ciudad'].label = 'Ciudad'
        self.fields['provincia'].label = 'Provincia'
        self.fields['codigo_postal'].label = 'Código Postal'
        self.fields['pais'].label = 'País'
        self.fields['es_predeterminada'].label = 'Establecer como dirección predeterminada'
