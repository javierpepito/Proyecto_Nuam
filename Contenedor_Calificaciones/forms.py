from django import forms
from .models import CalificacionTributaria, Empresa
from .validators import validate_rut_chileno, formatear_rut
from django.core.exceptions import ValidationError

class CalificacionTributariaForm(forms.ModelForm):
    """
    Formulario para crear/editar calificaciones tributarias.
    Solo muestra los campos que el usuario debe rellenar.
    """
    
    # Campo de texto para RUT (no FK directa)
    rut_empresa = forms.CharField(
        max_length=13,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'rut_empresa',
            'placeholder': 'Ej: 12345678-9',
            'aria-describedby': 'ayudaFormato'
        }),
        label='RUT de la Empresa',
        help_text='Debes ingresar el RUT sin puntos y con guión al final.'
    )
    
    class Meta:
        model = CalificacionTributaria
        fields = [
            'anio_tributario',
            'tipo_calificacion',
            'monto_tributario',
            'factor_tributario',
            'unidad_valor',
            'puntaje_calificacion',
            'categoria_calificacion',
            'nivel_riesgo',
            'justificacion_resultado',
        ]
        
        widgets = {
            'anio_tributario': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'anio_tributario',
                'placeholder': 'Ej: 2024',
                'min': 1900,
                'max': 2100
            }),
            'tipo_calificacion': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'tipo_calificacion',
                'placeholder': 'Ej: Anual, Trimestral'
            }),
            'monto_tributario': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'monto_tributario',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ej: 15000000.50'
            }),
            'factor_tributario': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'factor_tributario',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ej: 1.5'
            }),
            'unidad_valor': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'unidad_valor',
                'placeholder': 'Ej: CLP, UF, USD'
            }),
            'puntaje_calificacion': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'puntaje_calificacion',
                'min': '0',
                'max': '100',
                'placeholder': 'De 0 a 100'
            }),
            'categoria_calificacion': forms.Select(attrs={
                'class': 'form-control',
                'id': 'categoria_calificacion'
            }),
            'nivel_riesgo': forms.Select(attrs={
                'class': 'form-control',
                'id': 'nivel_riesgo'
            }),
            'justificacion_resultado': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'justificacion_resultado',
                'rows': 4,
                'placeholder': 'Observaciones sobre la calificación...'
            }),
        }
        
        labels = {
            'anio_tributario': 'Año Tributario',
            'tipo_calificacion': 'Tipo de Calificación',
            'monto_tributario': 'Monto Tributario',
            'factor_tributario': 'Factor Tributario',
            'unidad_valor': 'Unidad de Valor',
            'puntaje_calificacion': 'Puntaje de Calificación',
            'categoria_calificacion': 'Categoría de la Calificación',
            'nivel_riesgo': 'Nivel de Riesgo',
            'justificacion_resultado': 'Justificación del Resultado (Observaciones)',
        }
        
        help_texts = {
            'anio_tributario': 'Año del periodo tributario a calificar',
            'puntaje_calificacion': 'Puntaje de 0 a 100',
            'justificacion_resultado': 'Opcional. Detalles adicionales sobre la calificación',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['justificacion_resultado'].required = False
    
    def clean_rut_empresa(self):
        """Validar formato del RUT y que la empresa exista"""
        rut = self.cleaned_data.get('rut_empresa', '').strip()
        if not rut:
            raise forms.ValidationError("El RUT de la empresa es obligatorio")
        
        try:
            validate_rut_chileno(rut)
            rut_formateado = formatear_rut(rut)
        except ValidationError as e:
            raise forms.ValidationError(f"RUT inválido: {e.message}")
        
        # Validar que la empresa exista
        if not Empresa.objects.filter(empresa_rut=rut_formateado).exists():
            raise forms.ValidationError(
                f'La empresa con RUT {rut_formateado} no está registrada. '
                'Por favor, regístrela primero en la sección de Empresas.'
            )
        
        return rut_formateado