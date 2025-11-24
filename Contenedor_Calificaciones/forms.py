from django import forms
from .models import CalificacionTributaria, Empresa, Cuenta, CalificadorTributario, JefeEquipo
from .validators import validate_rut_chileno, formatear_rut
from django.core.exceptions import ValidationError
import re

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

class EmpresaForm(forms.ModelForm):
    """
    Formulario para registrar empresas.
    Valida RUT y evita duplicados.
    """
    class Meta:
        model = Empresa
        fields = ["empresa_rut", "nombre_empresa", "pais", "tipo_de_empresa"]
        
        widgets = {
            'empresa_rut': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 12.345.678-9',
                'id': 'id_empresa_rut'
            }),
            'nombre_empresa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre de la empresa',
                'id': 'id_nombre_empresa'
            }),
            'pais': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_pais'
            }),
            'tipo_de_empresa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: S.A., Limitada, SPA',
                'id': 'id_tipo_de_empresa'
            }),
        }
        
        labels = {
            'empresa_rut': 'RUT Empresa',
            'nombre_empresa': 'Nombre Empresa',
            'pais': 'País',
            'tipo_de_empresa': 'Tipo de Empresa',
        }
    
    def clean_empresa_rut(self):
        """Validar formato del RUT y que no exista ya"""
        rut = self.cleaned_data.get('empresa_rut', '').strip()
        
        if not rut:
            raise ValidationError('El RUT de la empresa es obligatorio.')
        
        try:
            validate_rut_chileno(rut)
            rut_formateado = formatear_rut(rut)
        except ValidationError as e:
            raise ValidationError(f'RUT inválido: {e.message}')
        
        # Verificar que no exista ya (solo en creación, no en edición)
        if not self.instance.pk:
            if Empresa.objects.filter(empresa_rut=rut_formateado).exists():
                raise ValidationError(f'Ya existe una empresa registrada con el RUT {rut_formateado}.')
        
        return rut_formateado
    
    def clean_nombre_empresa(self):
        """Capitalizar nombre de la empresa"""
        nombre = self.cleaned_data.get("nombre_empresa", "")
        return " ".join(p.capitalize() for p in nombre.strip().split())
    
    def clean_tipo_de_empresa(self):
        """Capitalizar tipo de empresa"""
        tipo = self.cleaned_data.get("tipo_de_empresa", "")
        return tipo.strip().upper()  # Ej: S.A., LIMITADA, SPA

class RegistroCuentaForm(forms.ModelForm):
    """
    Formulario para registro de nueva cuenta de usuario.
    Valida que el RUT pertenezca a un trabajador de NUAM.
    """
    
    # Campo adicional para confirmar contraseña
    confirmar_contrasena = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control password-input',
            'placeholder': 'Confirme su Contraseña',
            'id': 'id_confirmar_contrasena'
        }),
        label='Confirmar Contraseña'
    )
    
    class Meta:
        model = Cuenta
        fields = ['rut', 'nombre', 'apellido', 'direccion', 'telefono', 'edad', 'correo', 'contrasena']
        widgets = {
            'rut': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 12.345.678-9',
                'id': 'id_rut'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su Nombre',
                'id': 'id_nombre'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su Apellido',
                'id': 'id_apellido'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su Dirección',
                'id': 'id_direccion'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '912345678',
                'id': 'id_telefono',
                'maxlength': '9',
                'pattern': '[0-9]{9}',
                'inputmode': 'numeric'
            }),
            'edad': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su Edad',
                'min': '18',
                'max': '100',
                'id': 'id_edad'
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@correo.com',
                'id': 'id_correo'
            }),
            'contrasena': forms.PasswordInput(attrs={
                'class': 'form-control password-input',
                'placeholder': 'Ingrese su Contraseña',
                'id': 'id_contrasena'
            }),
        }
        labels = {
            'rut': 'Rut',
            'nombre': 'Nombre',
            'apellido': 'Apellido',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'edad': 'Edad',
            'correo': 'Correo',
            'contrasena': 'Contraseña',
        }
    
    def clean_rut(self):
        """Validar formato del RUT y que pertenezca a un trabajador de NUAM"""
        rut = self.cleaned_data.get('rut', '').strip()
        if not rut:
            raise ValidationError('El RUT es obligatorio.')
        
        try:
            validate_rut_chileno(rut)
            rut_formateado = formatear_rut(rut)
        except ValidationError as e:
            raise ValidationError(f'RUT inválido: {e.message}')
        
        # Verificar que el RUT exista en CalificadorTributario o JefeEquipo
        es_calificador = CalificadorTributario.objects.filter(rut=rut_formateado).exists()
        es_jefe = JefeEquipo.objects.filter(rut=rut_formateado).exists()
        
        if not es_calificador and not es_jefe:
            raise ValidationError('Este RUT no está registrado como trabajador de NUAM.')
        
        # Verificar que no tenga cuenta ya creada
        if Cuenta.objects.filter(rut=rut_formateado).exists():
            raise ValidationError('Ya existe una cuenta con este RUT.')
        
        return rut_formateado
    
    def clean_telefono(self):
        """Validar que el teléfono tenga exactamente 9 dígitos"""
        telefono = self.cleaned_data.get('telefono', '').strip()
        
        # Eliminar espacios, guiones y otros caracteres
        telefono_limpio = re.sub(r'\D', '', telefono)
        
        if not telefono_limpio:
            raise ValidationError('El teléfono es obligatorio.')
        
        if len(telefono_limpio) != 9:
            raise ValidationError('El teléfono debe tener exactamente 9 dígitos.')
        
        if not telefono_limpio.isdigit():
            raise ValidationError('El teléfono solo puede contener números.')
        
        # Validar que empiece con 9 (celulares chilenos)
        if not telefono_limpio.startswith('9'):
            raise ValidationError('El teléfono debe comenzar con 9.')
        
        return telefono_limpio
    
    def clean_edad(self):
        """Validar que la edad sea válida"""
        edad = self.cleaned_data.get('edad')
        if edad:
            if edad < 18:
                raise ValidationError('Debes tener al menos 18 años.')
            if edad > 100:
                raise ValidationError('Por favor, ingresa una edad válida.')
        return edad
    
    def clean_contrasena(self):
        """Validar que la contraseña cumpla con los requisitos de seguridad"""
        contrasena = self.cleaned_data.get('contrasena')
        if contrasena:
            if len(contrasena) < 8:
                raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
            if not re.search(r'[A-Z]', contrasena):
                raise ValidationError('La contraseña debe contener al menos una letra mayúscula.')
            if not re.search(r'[a-z]', contrasena):
                raise ValidationError('La contraseña debe contener al menos una letra minúscula.')
            if not re.search(r'[0-9]', contrasena):
                raise ValidationError('La contraseña debe contener al menos un número.')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', contrasena):
                raise ValidationError('La contraseña debe contener al menos un símbolo especial.')
        return contrasena
    
    def clean(self):
        """Validar que las contraseñas coincidan"""
        cleaned_data = super().clean()
        contrasena = cleaned_data.get('contrasena')
        confirmar = cleaned_data.get('confirmar_contrasena')
        
        if contrasena and confirmar:
            if contrasena != confirmar:
                raise ValidationError({
                    'confirmar_contrasena': 'Las contraseñas no coinciden.'
                })
        
        return cleaned_data