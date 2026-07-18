from django import forms

from .models import ArticuloBlog, ConfiguracionSitio, DisenoCorreo, MensajeContacto, PreguntaFrecuente


class ArticuloBlogForm(forms.ModelForm):
    class Meta:
        model = ArticuloBlog
        fields = ('titulo', 'slug', 'resumen', 'contenido', 'imagen_url', 'publicado')
        widgets = {
            'resumen': forms.Textarea(attrs={'rows': 3}),
            'contenido': forms.Textarea(attrs={'rows': 14}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'


class ConfiguracionSitioForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionSitio
        exclude = ('actualizado',)
        widgets = {
            'texto_nosotros': forms.Textarea(attrs={'rows': 5}),
            'texto_filosofia': forms.Textarea(attrs={'rows': 5}),
            'texto_artesania': forms.Textarea(attrs={'rows': 5}),
            'texto_estudio': forms.Textarea(attrs={'rows': 4}),
            'texto_politica_envios': forms.Textarea(attrs={'rows': 5}),
            'texto_terminos': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class DisenoCorreoForm(forms.ModelForm):
    CAMPOS_COLOR = (
        'color_acento', 'color_fondo', 'color_contenido', 'color_superficie',
        'color_texto', 'color_texto_secundario', 'color_borde', 'color_pie',
        'color_texto_pie',
    )

    class Meta:
        model = DisenoCorreo
        exclude = ('actualizado',)
        widgets = {
            'texto_pie': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if nombre in self.CAMPOS_COLOR:
                field.widget = forms.TextInput(attrs={
                    'class': 'form-control email-color-text',
                    'data-color-field': nombre,
                    'maxlength': 7,
                })


class PreguntaFrecuenteForm(forms.ModelForm):
    class Meta:
        model = PreguntaFrecuente
        fields = ('pregunta', 'respuesta', 'orden', 'activa')
        widgets = {'respuesta': forms.Textarea(attrs={'rows': 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'


class MensajeContactoAdminForm(forms.ModelForm):
    class Meta:
        model = MensajeContacto
        fields = ('estado', 'notas_internas')
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'notas_internas': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
