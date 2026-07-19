import re

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.usuarios.forms import TELEFONO_RE, normalizar_texto_usuario

from .models import MetodoEnvio, PerfilUsuario


class CheckoutForm(forms.Form):
    METODOS_PAGO = (
        ('paypal', 'PayPal'),
        ('transferencia', 'Transferencia bancaria'),
        ('contra_entrega', 'Contra entrega'),
    )

    nombre_completo = forms.CharField(max_length=100)
    telefono = forms.CharField(max_length=20)
    direccion = forms.CharField(max_length=200)
    ciudad = forms.CharField(max_length=100)
    provincia = forms.CharField(max_length=100)
    codigo_postal = forms.CharField(max_length=10)
    metodo_envio = forms.ModelChoiceField(queryset=MetodoEnvio.objects.none())
    metodo_pago = forms.ChoiceField(choices=METODOS_PAGO)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['metodo_envio'].queryset = MetodoEnvio.objects.filter(activo=True)

    def clean_telefono(self):
        telefono = normalizar_texto_usuario(
            self.cleaned_data['telefono'], compactar_espacios=False
        )
        if not TELEFONO_RE.fullmatch(telefono):
            raise forms.ValidationError('Ingresa un número de teléfono válido.')
        return telefono

    def clean_codigo_postal(self):
        codigo = normalizar_texto_usuario(
            self.cleaned_data['codigo_postal'], compactar_espacios=False
        )
        if not re.fullmatch(r'[A-Za-z0-9 -]{2,10}', codigo):
            raise forms.ValidationError('Ingresa un código postal válido.')
        return codigo.upper()

    def clean(self):
        cleaned = super().clean()
        for campo in ('nombre_completo', 'direccion', 'ciudad', 'provincia'):
            if campo in cleaned:
                try:
                    cleaned[campo] = normalizar_texto_usuario(cleaned[campo])
                except forms.ValidationError as exc:
                    self.add_error(campo, exc)
        return cleaned


class EmpleadoCrearForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        validators=User._meta.get_field('username').validators,
    )
    email = forms.EmailField(max_length=254)
    password = forms.CharField(max_length=128, strip=False, widget=forms.PasswordInput)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    telefono = forms.CharField(max_length=20, required=False)
    direccion = forms.CharField(max_length=200, required=False)

    def clean_username(self):
        username = normalizar_texto_usuario(
            self.cleaned_data['username'], compactar_espacios=False
        )
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('No se pudo crear la cuenta con esos datos.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('No se pudo crear la cuenta con esos datos.')
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        try:
            validate_password(password)
        except ValidationError as exc:
            raise forms.ValidationError(exc.messages) from exc
        return password

    def clean_telefono(self):
        telefono = normalizar_texto_usuario(
            self.cleaned_data.get('telefono', ''), compactar_espacios=False
        )
        if telefono and not TELEFONO_RE.fullmatch(telefono):
            raise forms.ValidationError('Ingresa un número de teléfono válido.')
        return telefono

    def clean(self):
        cleaned = super().clean()
        for campo in ('first_name', 'last_name', 'direccion'):
            if campo in cleaned:
                try:
                    cleaned[campo] = normalizar_texto_usuario(cleaned[campo])
                except forms.ValidationError as exc:
                    self.add_error(campo, exc)
        return cleaned

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
        )
        PerfilUsuario.objects.create(
            usuario=user,
            tipo_usuario='empleado',
            telefono=self.cleaned_data['telefono'],
            direccion=self.cleaned_data['direccion'],
        )
        return user


class EmpleadoEditarForm(forms.Form):
    email = forms.EmailField(max_length=254)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    telefono = forms.CharField(max_length=20, required=False)
    direccion = forms.CharField(max_length=200, required=False)
    tipo_usuario = forms.ChoiceField(choices=PerfilUsuario.TIPO_USUARIO)

    def __init__(self, *args, usuario, **kwargs):
        self.usuario = usuario
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.usuario.pk).exists():
            raise forms.ValidationError('No se pudo guardar la cuenta con esos datos.')
        return email

    def clean_telefono(self):
        telefono = normalizar_texto_usuario(
            self.cleaned_data.get('telefono', ''), compactar_espacios=False
        )
        if telefono and not TELEFONO_RE.fullmatch(telefono):
            raise forms.ValidationError('Ingresa un número de teléfono válido.')
        return telefono

    def clean(self):
        cleaned = super().clean()
        for campo in ('first_name', 'last_name', 'direccion'):
            if campo in cleaned:
                try:
                    cleaned[campo] = normalizar_texto_usuario(cleaned[campo])
                except forms.ValidationError as exc:
                    self.add_error(campo, exc)
        return cleaned
