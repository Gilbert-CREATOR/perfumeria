import re
import unicodedata

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import PerfilUsuario, Direccion


User = get_user_model()
CONTROL_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
TELEFONO_RE = re.compile(r'^\+?[0-9() .-]{7,20}$')


def normalizar_texto_usuario(value, *, compactar_espacios=True):
    """Normaliza texto humano sin convertirlo en HTML ni alterar contraseñas."""
    value = unicodedata.normalize('NFKC', value or '').strip()
    if CONTROL_CHARS_RE.search(value):
        raise ValidationError('El valor contiene caracteres no permitidos.')
    if compactar_espacios:
        value = ' '.join(value.split())
    return value


class LoginSeguroForm(forms.Form):
    credencial = forms.CharField(max_length=254, strip=True)
    password = forms.CharField(max_length=128, strip=False, widget=forms.PasswordInput)

    def clean_credencial(self):
        return normalizar_texto_usuario(
            self.cleaned_data['credencial'], compactar_espacios=False
        )


class RegistroSeguroForm(UserCreationForm):
    email = forms.EmailField(required=True, max_length=254)
    first_name = forms.CharField(required=False, max_length=150)
    last_name = forms.CharField(required=False, max_length=150)
    terms_accepted = forms.BooleanField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limita también el coste de validar contraseñas enviadas deliberadamente enormes.
        self.fields['password1'].max_length = 128
        self.fields['password2'].max_length = 128

    def clean_username(self):
        username = normalizar_texto_usuario(
            self.cleaned_data['username'], compactar_espacios=False
        )
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('No se pudo crear la cuenta con esos datos.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('No se pudo crear la cuenta con esos datos.')
        return email

    def clean_first_name(self):
        return normalizar_texto_usuario(self.cleaned_data.get('first_name', ''))

    def clean_last_name(self):
        return normalizar_texto_usuario(self.cleaned_data.get('last_name', ''))

    def save(self, commit=True):
        # UserCreationForm usa set_password(); nunca asigna la contraseña al modelo.
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

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

    def clean_telefono(self):
        telefono = normalizar_texto_usuario(
            self.cleaned_data.get('telefono', ''), compactar_espacios=False
        )
        if telefono and not TELEFONO_RE.fullmatch(telefono):
            raise ValidationError('Ingresa un número de teléfono válido.')
        return telefono

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

    def clean_telefono(self):
        telefono = normalizar_texto_usuario(
            self.cleaned_data.get('telefono', ''), compactar_espacios=False
        )
        if not TELEFONO_RE.fullmatch(telefono):
            raise ValidationError('Ingresa un número de teléfono válido.')
        return telefono

    def clean_codigo_postal(self):
        codigo = normalizar_texto_usuario(
            self.cleaned_data.get('codigo_postal', ''), compactar_espacios=False
        )
        if not re.fullmatch(r'[A-Za-z0-9 -]{2,10}', codigo):
            raise ValidationError('Ingresa un código postal válido.')
        return codigo.upper()

    def clean(self):
        cleaned = super().clean()
        for campo in ('nombre_completo', 'direccion', 'ciudad', 'provincia', 'pais'):
            if campo in cleaned:
                try:
                    cleaned[campo] = normalizar_texto_usuario(cleaned[campo])
                except ValidationError as exc:
                    self.add_error(campo, exc)
        return cleaned
