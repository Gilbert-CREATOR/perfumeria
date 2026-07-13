import base64
from decimal import Decimal

from django import forms
from django.core.files.base import ContentFile
from django.db import OperationalError, ProgrammingError
from .models import Pedido, MetodoEnvio, Envio
from apps.productos.models import Producto
from apps.productos.image_processing import remove_uniform_background


class ProductoAdminForm(forms.ModelForm):
    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    eliminar_imagen = forms.BooleanField(
        required=False,
        label='Eliminar imagen actual',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    quitar_fondo = forms.BooleanField(
        required=False,
        initial=True,
        label='Quitar fondo uniforme automáticamente',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    temporada = forms.MultipleChoiceField(
        required=False,
        choices=(),
        label='Temporadas',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'admin-season-checkbox'}),
    )
    nueva_temporada = forms.CharField(
        required=False,
        max_length=200,
        label='Agregar temporadas nuevas',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej.: Primavera, Todo el año',
        }),
    )
    tipo = forms.ChoiceField(
        required=False,
        choices=(),
        label='Tipo',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    nuevo_tipo = forms.CharField(
        required=False,
        max_length=100,
        label='Agregar un tipo nuevo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej.: Serum, Crema corporal',
        }),
    )

    class Meta:
        model = Producto
        fields = [
            'nombre',
            'marca',
            'descripcion',
            'precio',
            'imagen',
            'tipo',
            'tamano_ml',
            'stock',
            'disponible',
            'temporada',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Opcional'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'tamano_ml': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        type_choices = list(Producto.TIPO_CHOICES)
        season_choices = list(Producto.TEMPORADA_CHOICES)

        # Las opciones creadas desde productos anteriores vuelven a aparecer
        # automáticamente en el formulario para poder reutilizarlas.
        try:
            known_types = Producto.objects.exclude(tipo='').values_list('tipo', flat=True).distinct()
            type_values = {value for value, _label in type_choices}
            for value in known_types:
                if value and value not in type_values:
                    type_choices.append((value, value))
                    type_values.add(value)

            season_values = {value for value, _label in season_choices}
            for values in Producto.objects.values_list('temporada', flat=True):
                if isinstance(values, str):
                    values = [values]
                for value in values or []:
                    if value and value not in season_values:
                        season_choices.append((value, value))
                        season_values.add(value)
        except (OperationalError, ProgrammingError):
            # Permite cargar el formulario mientras se crean las migraciones.
            pass

        self.fields['tipo'].choices = [('', 'Sin tipo')] + type_choices
        self.fields['temporada'].choices = season_choices

        # En productos nuevos se elimina el fondo por defecto. Al editar uno
        # existente, el administrador debe marcarlo para reprocesar la imagen
        # actual y así evitamos degradarla en cada guardado.
        if self.instance and self.instance.pk and self.instance.tiene_imagen():
            self.fields['quitar_fondo'].initial = False

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock in (None, ''):
            return 0
        if stock < 0:
            raise forms.ValidationError('El stock no puede ser negativo.')
        return stock

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        return Decimal('0') if precio in (None, '') else precio

    def clean_tamano_ml(self):
        tamano = self.cleaned_data.get('tamano_ml')
        return 0 if tamano in (None, '') else tamano

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        # Una imagen ya guardada es un FieldFile. En Render el archivo físico
        # puede haber desaparecido aunque conservemos la copia en PostgreSQL;
        # no se debe consultar `.size` en ese caso.
        if imagen and getattr(imagen, '_committed', False):
            return imagen
        if imagen and getattr(imagen, 'size', 0) > self.MAX_IMAGE_SIZE:
            raise forms.ValidationError('La imagen no puede superar 5 MB.')
        if imagen and getattr(imagen, 'content_type', '').split('/')[0] != 'image':
            raise forms.ValidationError('Selecciona un archivo de imagen válido.')
        if imagen and self.data.get('quitar_fondo'):
            try:
                imagen = remove_uniform_background(imagen)
            except (OSError, ValueError):
                raise forms.ValidationError('No se pudo procesar el fondo de esta imagen.')
        return imagen

    def save(self, commit=True):
        producto = super().save(commit=False)
        imagen = self.cleaned_data.get('imagen')
        imagen_nueva = imagen and not getattr(imagen, '_committed', False)

        if self.cleaned_data.get('eliminar_imagen'):
            if producto.imagen:
                producto.imagen.delete(save=False)
            producto.imagen = None
            producto.imagen_base64 = None
            producto.imagen_nombre = None
        elif (
            self.cleaned_data.get('quitar_fondo')
            and not imagen_nueva
            and producto.imagen_base64
        ):
            imagen_actual = ContentFile(
                base64.b64decode(producto.imagen_base64),
                name=producto.imagen_nombre or f'producto_{producto.pk}.png',
            )
            producto.imagen = remove_uniform_background(imagen_actual)

        if commit:
            producto.save()
            self.save_m2m()
        return producto

    def clean(self):
        cleaned_data = super().clean()
        nuevo_tipo = (cleaned_data.get('nuevo_tipo') or '').strip()
        if nuevo_tipo:
            cleaned_data['tipo'] = nuevo_tipo

        temporadas = list(cleaned_data.get('temporada') or [])
        nuevas_temporadas = (cleaned_data.get('nueva_temporada') or '').split(',')
        for temporada in nuevas_temporadas:
            temporada = temporada.strip()
            if temporada and temporada not in temporadas:
                temporadas.append(temporada)
        cleaned_data['temporada'] = temporadas

        imagen = cleaned_data.get('imagen')
        imagen_nueva = imagen and not getattr(imagen, '_committed', False)
        if cleaned_data.get('eliminar_imagen') and imagen_nueva:
            self.add_error(
                'imagen',
                'No puedes subir y eliminar una imagen al mismo tiempo. Elige una opción.',
            )
        if cleaned_data.get('stock', 0) == 0:
            cleaned_data['disponible'] = False
        return cleaned_data


class PedidoAdminForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['estado', 'metodo_pago']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
        }

class MetodoEnvioForm(forms.ModelForm):
    class Meta:
        model = MetodoEnvio
        fields = ['nombre', 'descripcion', 'costo', 'tiempo_entrega', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tiempo_entrega': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProductoStockForm(forms.ModelForm):
    stock = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Producto
        fields = ['stock', 'disponible']
        widgets = {
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_stock(self):
        return self.cleaned_data.get('stock') or 0

class EnvioForm(forms.ModelForm):
    class Meta:
        model = Envio
        fields = ['metodo_envio', 'numero_seguimiento', 'estado', 'fecha_entrega_estimada', 'notas']
        widgets = {
            'metodo_envio': forms.Select(attrs={'class': 'form-select'}),
            'numero_seguimiento': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'fecha_entrega_estimada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
