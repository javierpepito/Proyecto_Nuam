from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, EmailValidator
import re
from .validators import validate_rut_chileno, formatear_rut
from django.utils import timezone

# Modelos para importarlos a la base de datos en Supabase
# Modelo de calificadores tributarios

class CalificadorTributario(models.Model):
	rut = models.CharField(primary_key=True, max_length=13, validators=[validate_rut_chileno])  # 13 para soportar formato con puntos y guion
	fecha_ingreso = models.DateField()
	rol = models.CharField(max_length=50, editable=False)

	class Meta:
		# Nombre de la tabla en la base de datos Supabase
		db_table = 'calificador_tributario'
		# Nombre para las interfaces humanas como admin, etc.
		verbose_name = 'Calificador tributario'
		# Nombre para la forma prural en los filtros de admin.
		verbose_name_plural = 'Calificadores tributarios'

	def __str__(self) -> str:
		return self.rut

	def clean(self):
		# Valida y da formato estándar al RUT; capitaliza el rol
		if self.rut:
			validate_rut_chileno(self.rut)
			self.rut = formatear_rut(self.rut)
		# Asigna rol fijo por tipo de registro
		self.rol = "Calificador Tributario"

	def save(self, *args, **kwargs):
		# Asegura rol por defecto antes de validar campos requeridos
		if not self.rol:
			self.rol = "Calificador Tributario"
		self.full_clean()
		super().save(*args, **kwargs)



# Modelo de jefes de equipo

class JefeEquipo(models.Model):
	rut = models.CharField(primary_key=True, max_length=13, validators=[validate_rut_chileno])  # 13 para soportar formato con puntos y guion
	fecha_ingreso = models.DateField()
	rol = models.CharField(max_length=50, editable=False)

	class Meta:
		# Nombre de la tabla en la base de datos Supabase
		db_table = 'jefe_equipo'
		# Nombre para las interfaces humanas como admin, etc.
		verbose_name = 'Jefe de equipo'
		# Nombre para la forma prural en los filtros de admin.
		verbose_name_plural = 'Jefes de equipo'

	def __str__(self) -> str:
		return self.rut

	def clean(self):
		if self.rut:
			validate_rut_chileno(self.rut)
			self.rut = formatear_rut(self.rut)
		# Asigna rol fijo por tipo de registro
		self.rol = "Jefe De Equipo"

	def save(self, *args, **kwargs):
		if not self.rol:
			self.rol = "Jefe De Equipo"
		self.full_clean()
		super().save(*args, **kwargs)





# Modelo de equipos de trabajo

class EquipoDeTrabajo(models.Model):
	equipo_id = models.AutoField(primary_key=True)
	# Un equipo puede estar temporalmente sin jefe asignado
	jefe_equipo_rut = models.OneToOneField(
		JefeEquipo,
		on_delete=models.PROTECT,
		db_column='jefe_equipo_rut',
		to_field='rut',
		null=True,
		blank=True,
	)
	# Hasta 5 calificadores por equipo mediante relación intermedia
	calificadores = models.ManyToManyField(
		CalificadorTributario,
		through='EquipoCalificador',
		related_name='equipos_de_trabajo',
		help_text='Máximo 5 calificadores por equipo Mas El Jefe de equipo.',
	)

	class Meta:
		# Nombre de la tabla en la base de datos Supabase
		db_table = 'equipo_de_trabajo'
		# Nombre para las interfaces humanas como admin, etc.
		verbose_name = 'Equipo de trabajo'
		# Nombre para la forma prural en los filtros de admin.
		verbose_name_plural = 'Equipos de trabajo'

	def __str__(self) -> str:
		return f"Equipo {self.equipo_id}"





# Modelo intermedio para agregar a los calificadores y crear un equipo y luego enviar ese equipo al equipo de trabajo
# Para que en caso de desea eliminar un calificador no se elimine el equipo completo y evitar furos errores, esto me lo recomendo chat gpt

class EquipoCalificador(models.Model):
	equipo = models.ForeignKey(EquipoDeTrabajo, on_delete=models.PROTECT, db_column='equipo_id', related_name='rel_calificadores')
	# Un calificador solo puede estar en un equipo. Se garantiza con unique_together; se quita unique=True para evitar problemas de formulario.
	calificador = models.ForeignKey(CalificadorTributario, on_delete=models.PROTECT, db_column='calificador_tributario_rut', to_field='rut', related_name='rel_equipos')

	class Meta:
		db_table = 'equipo_calificador'
		unique_together = ('equipo', 'calificador')
		verbose_name = 'Calificador en equipo'
		verbose_name_plural = 'Calificadores en equipos'

	def clean(self):
		# No permitir más de 5 calificadores por equipo, esto se puede cambiar en caso de ser necesario
		if self.equipo_id:
			qs = EquipoCalificador.objects.filter(equipo=self.equipo)
			if self.pk:
				qs = qs.exclude(pk=self.pk)
			if qs.count() >= 5:
				raise ValidationError('Un equipo no puede tener más de 5 calificadores tributarios (máximo 6 integrantes incluyendo al jefe).')
		# Evitar que el calificador pertenezca a otro equipo distinto
		if self.calificador_id:
			existe_otro = EquipoCalificador.objects.filter(calificador=self.calificador).exclude(pk=self.pk).exists()
			if existe_otro:
				raise ValidationError('Este calificador ya pertenece a otro equipo.')

	def save(self, *args, **kwargs):
		self.full_clean()
		super().save(*args, **kwargs)




# Modelo de cuentas de trabajadores (solo trabajadores ya registrados como JefeEquipo o CalificadorTributario)

class Cuenta(models.Model):
	cuenta_id = models.AutoField(primary_key=True)
	rut = models.CharField(max_length=13, unique=True, validators=[validate_rut_chileno])  # 13 para soportar formato con puntos y guion
	# Rol se pone automatico segun a la tabla que pertenece el rut según el RUT (Jefe o Calificador) y no es editable
	rol = models.CharField(max_length=50, editable=False)
	# Tambien Se autoasigna según el RUT; el usuario no lo ve ni lo rellena.
	equipo_trabajo = models.ForeignKey(EquipoDeTrabajo, on_delete=models.PROTECT, db_column='equipo_trabajo_id', related_name='cuentas', editable=False, null=True, blank=True)
	nombre = models.CharField(max_length=100)
	apellido = models.CharField(max_length=100)
	telefono = models.CharField(max_length=25, blank=True, null=True, help_text='Número de teléfono celular')
	correo = models.EmailField(validators=[EmailValidator(message='Formato de correo inválido')])
	direccion = models.CharField(max_length=200, blank=True, null=True)
	edad = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(150)])
	contrasena = models.CharField(max_length=128, help_text='Debe tener mínimo 8 caracteres, una mayúscula, un número y un símbolo.')

	class Meta:
		db_table = 'cuenta'
		indexes = [
			models.Index(fields=["rut"], name="idx_cuenta_rut"),
		]
		verbose_name = 'Cuenta'
		verbose_name_plural = 'Cuentas'

	def __str__(self) -> str:
		return f"Cuenta {self.cuenta_id} - {self.rut}"

	def _capitalizar_nombre(self, valor: str) -> str:
		return " ".join(p.capitalize() for p in valor.strip().split()) if valor else valor

	def _validar_contrasena(self, pwd: str):
		if len(pwd) < 8:
			raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
		if not re.search(r'[A-Z]', pwd):
			raise ValidationError('La contraseña debe incluir al menos una letra mayúscula.')
		if not re.search(r'\d', pwd):
			raise ValidationError('La contraseña debe incluir al menos un número.')
		if not re.search(r'[^A-Za-z0-9]', pwd):
			raise ValidationError('La contraseña debe incluir al menos un símbolo.')

	def clean(self):
		# Validar y formatear RUT.
		if self.rut:
			validate_rut_chileno(self.rut)
			self.rut = formatear_rut(self.rut)

		# Determinar rol tomando el valor real del registro origen
		es_jefe = False
		es_calificador = False
		try:
			jefe = JefeEquipo.objects.get(rut=self.rut)
			es_jefe = True
			self.rol = jefe.rol  # Copiamos exactamente el rol almacenado
		except JefeEquipo.DoesNotExist:
			try:
				cal = CalificadorTributario.objects.get(rut=self.rut)
				es_calificador = True
				self.rol = cal.rol  # Copiamos exactamente el rol almacenado
			except CalificadorTributario.DoesNotExist:
				raise ValidationError('El RUT no está registrado como Jefe de equipo ni Calificador tributario.')

		# Seguridad: si por alguna razón no se asignó rol
		if not self.rol:
			self.rol = 'Jefe De Equipo' if es_jefe else 'Calificador Tributario'

		# Autoasignar equipo si se encuentra relación; permitir None
		if not self.equipo_trabajo_id:
			if es_jefe:
				try:
					self.equipo_trabajo = EquipoDeTrabajo.objects.get(jefe_equipo_rut__rut=self.rut)
				except EquipoDeTrabajo.DoesNotExist:
					self.equipo_trabajo = None
			else:
				try:
					rel = EquipoCalificador.objects.get(calificador__rut=self.rut)
					self.equipo_trabajo = rel.equipo
				except EquipoCalificador.DoesNotExist:
					self.equipo_trabajo = None
		else:
			# Si viene seteado (por código), validar coherencia.
			if es_jefe and self.equipo_trabajo and self.equipo_trabajo.jefe_equipo_rut and self.equipo_trabajo.jefe_equipo_rut.rut != self.rut:
				raise ValidationError('El RUT corresponde a un Jefe que no lidera ese equipo.')
			if es_calificador and self.equipo_trabajo and not EquipoCalificador.objects.filter(equipo=self.equipo_trabajo, calificador__rut=self.rut).exists():
				raise ValidationError('El Calificador no pertenece a ese equipo.')

		# Capitalizar nombre y apellido.
		if self.nombre:
			self.nombre = self._capitalizar_nombre(self.nombre)
		if self.apellido:
			self.apellido = self._capitalizar_nombre(self.apellido)

		# Validar contraseña.
		if self.contrasena:
			self._validar_contrasena(self.contrasena)
		else:
			raise ValidationError('La contraseña es obligatoria.')

	def save(self, *args, **kwargs):
		# Ejecuta clean para asegurar autoasignación antes de validar requeridos.
		self.full_clean()
		# atencion¡¡¡¡¡¡ Para ambiente real se debe usar hashing (Django auth). Aquí se guarda tal cual por requerimiento.
		super().save(*args, **kwargs)




# Modelo de empresas registradas por trabajadores

class Empresa(models.Model):
	empresa_rut = models.CharField(primary_key=True, max_length=13, validators=[validate_rut_chileno])
	nombre_empresa = models.CharField(max_length=150)
	ingresado_por = models.ForeignKey(Cuenta, on_delete=models.PROTECT, db_column='ingresado_por_id', related_name='empresas')
	ingresado_por_rut = models.CharField(max_length=13, editable=False)
	fecha_ingreso = models.DateTimeField(auto_now_add=True)
	PAIS_CHOICES = (
		('Chile', 'Chile'),
		('Colombia', 'Colombia'),
		('Peru', 'Perú'),
	)
	pais = models.CharField(max_length=10, choices=PAIS_CHOICES)
	tipo_de_empresa = models.CharField(max_length=100)

	class Meta:
		db_table = 'empresa'
		verbose_name = 'Empresa'
		verbose_name_plural = 'Empresas'

	def __str__(self) -> str:
		return f"{self.nombre_empresa} ({self.empresa_rut})"

	def clean(self):
		# Validar y formatear RUT de la empresa
		if self.empresa_rut:
			validate_rut_chileno(self.empresa_rut)
			self.empresa_rut = formatear_rut(self.empresa_rut)
		# Capitalizar nombre empresa palabra por palabra
		if self.nombre_empresa:
			self.nombre_empresa = " ".join(p.capitalize() for p in self.nombre_empresa.strip().split())
		# Asegurar coincidencia de rut de la cuenta ingresada
		if self.ingresado_por_id and self.ingresado_por:
			self.ingresado_por_rut = self.ingresado_por.rut

	def save(self, *args, **kwargs):
		self.full_clean()
		super().save(*args, **kwargs)


#Modelo de Calificaciones Tributarias
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class CalificacionTributaria(models.Model):
    # Choices para campos con opciones limitadas
    CATEGORIA_CHOICES = [
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
    ]
    
    NIVEL_RIESGO_CHOICES = [
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('critico', 'Crítico'),
    ]
    
    METODO_CHOICES = [
        ('masiva', 'Masiva'),
        ('manual', 'Manual'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('por_aprobar', 'Por Aprobar'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('eliminado', 'Eliminado'),
        ('mal_ingresada', 'Mal Ingresada'),
    ]
    
    # ==================== DATOS FANTASMAS (Auto-generados) ====================
    calificacion_id = models.AutoField(
        primary_key=True,
        verbose_name='ID Calificación'
    )
    
    # FK a tu modelo Cuenta personalizado
    cuenta_id = models.ForeignKey(
        'Contenedor_Calificaciones.Cuenta', 
        on_delete=models.PROTECT,
        db_column='cuenta_id',
        related_name='calificaciones',
        verbose_name='Cuenta',
        help_text='Usuario que crea la calificación',
        editable=False  
    )
    
    metodo_calificacion = models.CharField(
        max_length=10,
        choices=METODO_CHOICES,
        default='manual',
        verbose_name='Método de Calificación',
        editable=False  # Dato fantasma
    )
    
    fecha_calculo = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Cálculo',
        help_text='Fecha y hora en que se realizó el cálculo',
        editable=False  # Dato fantasma
    )
    
    estado_calificacion = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado de la Calificación',
        editable=False  # Dato fantasma
    )
    
    # ==================== DATOS DEL USUARIO ====================
    # FK a tu modelo Empresa
    rut_empresa = models.ForeignKey(
        'Contenedor_Calificaciones.Empresa',  
        on_delete=models.PROTECT,
        db_column='empresa_rut',
        to_field='empresa_rut',
        related_name='calificaciones',
        verbose_name='RUT Empresa',
        help_text='Empresa a calificar'
    )
    
    # Campo desnormalizado para rendimiento (se auto-completa)
    nombre_empresa = models.CharField(
        max_length=255,
        verbose_name='Nombre Empresa',
        editable=False,  # Se auto-completa desde Empresa
        blank=True
    )
    
    anio_tributario = models.IntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(2100)
        ],
        verbose_name='Año Tributario',
        help_text='Año del periodo tributario'
    )
    
    tipo_calificacion = models.CharField(
        max_length=100,
        verbose_name='Tipo de Calificación',
        help_text='Tipo o categoría de la calificación tributaria'
    )
    
    monto_tributario = models.FloatField(
        validators=[MinValueValidator(0)],
        verbose_name='Monto Tributario',
        help_text='Monto en valor monetario'
    )
    
    factor_tributario = models.FloatField(
        validators=[MinValueValidator(0)],
        verbose_name='Factor Tributario'
    )
    
    unidad_valor = models.CharField(
        max_length=50,
        verbose_name='Unidad de Valor',
        help_text='Unidad de medida del valor (CLP, UF, USD, etc.)'
    )
    
    puntaje_calificacion = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        verbose_name='Puntaje de Calificación',
        help_text='Puntaje de 0 a 100'
    )
    
    categoria_calificacion = models.CharField(
        max_length=10,
        choices=CATEGORIA_CHOICES,
        verbose_name='Categoría de Calificación'
    )
    
    nivel_riesgo = models.CharField(
        max_length=10,
        choices=NIVEL_RIESGO_CHOICES,
        verbose_name='Nivel de Riesgo'
    )
    
    justificacion_resultado = models.TextField(
        verbose_name='Justificación del Resultado',
        help_text='Descripción o justificación de la calificación obtenida',
        blank=True,
        null=True
    )
    
    # ==================== METADATA ====================
    class Meta:
        db_table = 'calificacion_tributaria'
        verbose_name = 'Calificación Tributaria'
        verbose_name_plural = 'Calificaciones Tributarias'
        ordering = ['-fecha_calculo']
        indexes = [
            models.Index(fields=['anio_tributario'], name='idx_calificacion_anio'),
            models.Index(fields=['estado_calificacion'], name='idx_calificacion_estado'),
            models.Index(fields=['-fecha_calculo'], name='idx_calificacion_fecha'),
            models.Index(fields=['cuenta_id'], name='idx_calificacion_cuenta'),
        ]
        # Evitar duplicados: una empresa solo puede tener una calificación por año y tipo
        unique_together = [['anio_tributario', 'tipo_calificacion']]
    
    def __str__(self):
        return f"{self.nombre_empresa} - {self.anio_tributario} ({self.puntaje_calificacion}pts)"
    
    def clean(self):
        """
        Validaciones personalizadas antes de guardar
        """
        from django.core.exceptions import ValidationError
        
        # Validar que el año tributario no sea futuro
        if self.anio_tributario and self.anio_tributario > timezone.now().year:
            raise ValidationError({
                'anio_tributario': 'El año tributario no puede ser mayor al año actual.'
            })
        
        super().clean()
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para lógica automática
        """
        # Ejecutar validaciones
        self.full_clean()
        
        # Si es un nuevo registro, actualizar fecha_calculo
        if not self.pk:
            self.fecha_calculo = timezone.now()
        
        super().save(*args, **kwargs)