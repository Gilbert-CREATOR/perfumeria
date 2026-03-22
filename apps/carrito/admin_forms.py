from django import forms
from .models import Pedido, MetodoEnvio, Envio
from apps.productos.models import Producto


class ProductoAdminForm(forms.ModelForm):
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
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'tamano_ml': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'temporada': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_stock(self):
        stock = self.cleaned_data['stock']
        if stock < 0:
            raise forms.ValidationError('El stock no puede ser negativo.')
        return stock

    def clean(self):
        cleaned_data = super().clean()
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
