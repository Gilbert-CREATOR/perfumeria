import base64

from django import forms
from django.core.files.base import ContentFile
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
        choices=Producto.TEMPORADA_CHOICES,
        label='Temporadas',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'admin-season-checkbox'}),
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
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'tamano_ml': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # En productos nuevos se elimina el fondo por defecto. Al editar uno
        # existente, el administrador debe marcarlo para reprocesar la imagen
        # actual y así evitamos degradarla en cada guardado.
        if self.instance and self.instance.pk and self.instance.tiene_imagen():
            self.fields['quitar_fondo'].initial = False

    def clean_stock(self):
        stock = self.cleaned_data['stock']
        if stock < 0:
            raise forms.ValidationError('El stock no puede ser negativo.')
        return stock

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
    class Meta:
        model = Producto
        fields = ['stock', 'disponible']
        widgets = {
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

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
