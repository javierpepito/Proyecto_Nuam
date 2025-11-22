from django import forms
from .models import CalificacionTributaria, Empresa

class CalificacionTributariaForm(forms.ModelForm):
    """
    Formulario para crear/editar calificaciones tributarias.
    Solo muestra los campos que el usuario debe rellenar.
    """
    
    class Meta:
        model = CalificacionTributaria
        fields = [
            'rut_empresa',
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
            'rut_empresa': forms.Select(attrs={
                'class': 'form-control',
                'id': 'rut_empresa'
            }),
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
            'rut_empresa': 'RUT de la Empresa',
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
        """
        Personalizar el formulario al inicializarse
        """
        super().__init__(*args, **kwargs)
        
        # Hacer justificacion_resultado opcional
        self.fields['justificacion_resultado'].required = False
        
        # Filtrar empresas para mostrar solo las activas (si aplica)
        self.fields['rut_empresa'].queryset = Empresa.objects.all().order_by('nombre_empresa')
        
        # Personalizar el label del select de empresa
        self.fields['rut_empresa'].label_from_instance = lambda obj: f"{obj.nombre_empresa} ({obj.empresa_rut})"