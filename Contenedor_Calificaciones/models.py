from django.db import models
from django.core.exceptions import ValidationError
from .validators import validate_rut_chileno, formatear_rut

# Modelos para importarlos a la base de datos en Supabase
class CalificadorTributario(models.Model):
	rut = models.CharField(primary_key=True, max_length=12, validators=[validate_rut_chileno])
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


class JefeEquipo(models.Model):
	rut = models.CharField(primary_key=True, max_length=12, validators=[validate_rut_chileno])
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


class EquipoDeTrabajo(models.Model):
	equipo_id = models.AutoField(primary_key=True)
	# Un jefe solo puede pertenecer a un equipo (1 a 1)
	jefe_equipo_rut = models.OneToOneField(
		JefeEquipo,
		on_delete=models.PROTECT,
		db_column='jefe_equipo_rut',
		to_field='rut',
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
	# Un calificador solo puede estar en un equipo, por eso unique=True
	calificador = models.ForeignKey(CalificadorTributario, on_delete=models.PROTECT, db_column='calificador_tributario_rut', to_field='rut', related_name='rel_equipos', unique=True)

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


