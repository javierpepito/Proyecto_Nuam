from django.contrib import admin, messages
from .models import CalificadorTributario, JefeEquipo, EquipoDeTrabajo, EquipoCalificador


@admin.register(CalificadorTributario)
class CalificadorTributarioAdmin(admin.ModelAdmin):
	# Columnas visibles en la lista del admin
	list_display = ("rut", "fecha_ingreso", "rol")
	# Permite buscar por RUT en el admin
	search_fields = ("rut",)
	# Acción personalizada para ascender a Jefe de equipo
	actions = ["ascender_a_jefe"]

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


@admin.register(JefeEquipo)
class JefeEquipoAdmin(admin.ModelAdmin):
	# Configuración de columnas y búsqueda para los jefes
	list_display = ("rut", "fecha_ingreso", "rol")
	search_fields = ("rut",)


class EquipoCalificadorInline(admin.TabularInline):
	# Inline para editar la relación intermedia (equipo <-> calificador)
	model = EquipoCalificador
	extra = 0


@admin.register(EquipoDeTrabajo)
class EquipoDeTrabajoAdmin(admin.ModelAdmin):
	# Muestra el jefe del equipo y un contador de calificadores
	list_display = ("equipo_id", "jefe_equipo_rut", "calificadores_count")
	search_fields = ("equipo_id", "jefe_equipo_rut__rut")
	# Permite gestionar los calificadores desde el detalle del equipo
	inlines = [EquipoCalificadorInline]

	def calificadores_count(self, obj):
		"""Devuelve la cantidad de calificadores asociados al equipo."""
		return obj.calificadores.count()

	calificadores_count.short_description = "Calificadores"

