from django.contrib import admin, messages
from .models import CalificadorTributario, JefeEquipo, EquipoDeTrabajo, EquipoCalificador, Cuenta


@admin.register(CalificadorTributario)
class CalificadorTributarioAdmin(admin.ModelAdmin):
	# Columnas visibles en la lista del admin
	list_display = ("rut", "fecha_ingreso", "rol")
	# Permite buscar por RUT en el admin
	search_fields = ("rut",)
	# Acción personalizada para ascender a Jefe de equipo
	actions = ["ascender_a_jefe", "liberar_de_equipo"]

	def ascender_a_jefe(self, request, queryset):
		
		#Crea registros en JefeEquipo a partir de los calificados seleccionados.
		#Si ya existe un Jefe con el mismo RUT, se omite.
		#Copia la fecha de ingreso del calificador.
		#El campo `rol` del modelo JefeEquipo se fija automáticamente en el modelo.
		
		creados = 0
		omitidos = 0
		for cal in queryset:
			if JefeEquipo.objects.filter(rut=cal.rut).exists():
				omitidos += 1
				continue
			JefeEquipo.objects.create(rut=cal.rut, fecha_ingreso=cal.fecha_ingreso)
			creados += 1

		if creados:
			self.message_user(request, f"{creados} calificador(es) ascendidos a Jefe de equipo.", level=messages.SUCCESS)
		if omitidos:
			self.message_user(request, f"{omitidos} ya eran Jefe de equipo y se omitieron.", level=messages.WARNING)

	ascender_a_jefe.short_description = "Ascender a Jefe de equipo"

	def liberar_de_equipo(self, request, queryset):
		"""Elimina la relación EquipoCalificador si existe y libera al trabajador de su equipo."""
		from .models import EquipoCalificador, Cuenta
		liberados = 0
		omitidos = 0
		for cal in queryset:
			rel = EquipoCalificador.objects.filter(calificador=cal).first()
			if rel:
				rel.delete()  # Signal post_delete limpiará la cuenta
				Cuenta.objects.filter(rut=cal.rut).update(equipo_trabajo=None)
				liberados += 1
			else:
				omitidos += 1
		if liberados:
			self.message_user(request, f"{liberados} calificador(es) liberado(s) del equipo.", level=messages.SUCCESS)
		if omitidos:
			self.message_user(request, f"{omitidos} no estaban asignados a ningún equipo.", level=messages.WARNING)

	liberar_de_equipo.short_description = "Liberar del equipo"


@admin.register(JefeEquipo)
class JefeEquipoAdmin(admin.ModelAdmin):
	# Configuración de columnas y búsqueda para los jefes
	list_display = ("rut", "fecha_ingreso", "rol")
	search_fields = ("rut",)
	actions = ["liberar_de_equipo"]

	def liberar_de_equipo(self, request, queryset):
		"""Quita al jefe del equipo que lidera (si existe) dejando el equipo sin jefe."""
		from .models import EquipoDeTrabajo, Cuenta
		liberados = 0
		omitidos = 0
		for jefe in queryset:
			equipo = EquipoDeTrabajo.objects.filter(jefe_equipo_rut=jefe).first()
			if equipo:
				# Quitar jefe y actualizar cuenta mediante signals
				equipo.jefe_equipo_rut = None
				equipo.save()
				Cuenta.objects.filter(rut=jefe.rut).update(equipo_trabajo=None)
				liberados += 1
			else:
				omitidos += 1
		if liberados:
			self.message_user(request, f"{liberados} jefe(s) liberado(s) de su equipo.", level=messages.SUCCESS)
		if omitidos:
			self.message_user(request, f"{omitidos} no lideraban ningún equipo.", level=messages.WARNING)

	liberar_de_equipo.short_description = "Liberar del equipo"


class EquipoCalificadorInline(admin.TabularInline):
	# Inline para editar la relación intermedia (equipo <-> calificador)
	model = EquipoCalificador
	extra = 0

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		# Limita el listado de calificadores a los que aún no están asignados a un equipo
		if db_field.name == 'calificador':
			usados = EquipoCalificador.objects.values_list('calificador__rut', flat=True)
			kwargs['queryset'] = CalificadorTributario.objects.exclude(rut__in=usados)
		return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(EquipoDeTrabajo)
class EquipoDeTrabajoAdmin(admin.ModelAdmin):
	# Muestra el jefe del equipo y un contador de calificadores
	list_display = ("equipo_id", "jefe_equipo_rut", "calificadores_count")
	search_fields = ("equipo_id", "jefe_equipo_rut__rut")
	# Permite gestionar los calificadores desde el detalle del equipo
	inlines = [EquipoCalificadorInline]

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		# Limita el listado de jefes a aquellos que aún no lideran un equipo
		if db_field.name == 'jefe_equipo_rut':
			usados = EquipoDeTrabajo.objects.values_list('jefe_equipo_rut__rut', flat=True)
			kwargs['queryset'] = JefeEquipo.objects.exclude(rut__in=usados)
		return super().formfield_for_foreignkey(db_field, request, **kwargs)

	def calificadores_count(self, obj):
		"""Devuelve la cantidad de calificadores asociados al equipo."""
		return obj.calificadores.count()

	calificadores_count.short_description = "Calificadores"


## Modelo Rol eliminado: el rol ahora se deriva automáticamente por RUT en Cuenta


@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
	# Mostrar datos clave; equipo y rol se calculan automáticamente
	list_display = ("cuenta_id", "rut", "rol", "equipo_trabajo", "nombre", "apellido", "edad", "correo")
	search_fields = ("rut", "nombre", "apellido", "correo")
	readonly_fields = ("rol", "equipo_trabajo")

	def get_fields(self, request, obj=None):
		# Orden de campos en el formulario excluyendo lo que se autocompleta
		base = ["rut", "nombre", "apellido", "telefono", "correo", "direccion", "edad", "contrasena"]
		# Mostrar rol y equipo como solo lectura si ya existen
		if obj:
			base += ["rol", "equipo_trabajo"]
		return base

	def save_model(self, request, obj, form, change):
		# Delegar lógica al modelo (autoasignaciones en clean())
		obj.save()

