from django.contrib import admin, messages
from .models import CalificadorTributario, JefeEquipo, EquipoDeTrabajo, EquipoCalificador, Cuenta, Empresa


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
	verbose_name = "Miembro del equipo"
	verbose_name_plural = "Miembros del equipo"
	can_delete = True
	show_change_link = True
	# Permitir agregar calificadores
	def has_add_permission(self, request, obj=None):
		return True
	def has_change_permission(self, request, obj=None):
		return True
	def has_delete_permission(self, request, obj=None):
		return True

	# Eliminar filtro restrictivo en formfield_for_foreignkey para mostrar todos los calificadores disponibles
	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if db_field.name == 'calificador':
			from .models import CalificadorTributario, Cuenta
			qs = CalificadorTributario.objects.all().order_by('rut')
			kwargs['queryset'] = qs
			from django import forms
			class NombreCalificadorChoiceField(forms.ModelChoiceField):
				def label_from_instance(self, obj):
					cuenta = Cuenta.objects.filter(rut=obj.rut).first()
					if cuenta:
						nombre = f"{cuenta.nombre} {cuenta.apellido}".strip()
						return nombre if nombre else obj.rut
					return obj.rut
			kwargs['form_class'] = NombreCalificadorChoiceField
		return super().formfield_for_foreignkey(db_field, request, **kwargs)
	class Media:
		css = {
			'all': ('Contenedor_Calificaciones/admin/hide_inline_icons.css',)
		}

	# Mostrar nombre completo en vez de RUT en el selector
	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if db_field.name == 'calificador':
			object_id = request.resolver_match.kwargs.get('object_id')
			if object_id:
				usados_en_otros = EquipoCalificador.objects.exclude(equipo_id=object_id).values_list('calificador__rut', flat=True)
				qs = CalificadorTributario.objects.exclude(rut__in=usados_en_otros)
			else:
				usados = EquipoCalificador.objects.values_list('calificador__rut', flat=True)
				qs = CalificadorTributario.objects.exclude(rut__in=usados)
			qs = qs.order_by('rut')
			kwargs['queryset'] = qs
			from django import forms
			from .models import Cuenta
			class NombreCalificadorChoiceField(forms.ModelChoiceField):
				def label_from_instance(self, obj):
					cuenta = Cuenta.objects.filter(rut=obj.rut).first()
					if cuenta:
						nombre = f"{cuenta.nombre} {cuenta.apellido}".strip()
						return nombre if nombre else obj.rut
					return obj.rut
			kwargs['form_class'] = NombreCalificadorChoiceField
		return super().formfield_for_foreignkey(db_field, request, **kwargs)



@admin.register(EquipoDeTrabajo)
class EquipoDeTrabajoAdmin(admin.ModelAdmin):
	# Muestra el nombre del equipo (o ID si no tiene nombre), jefe y un contador de calificadores
	list_display = ("nombre_o_id", "jefe_nombre", "miembros_equipo", "calificadores_count")
	list_display_links = ("nombre_o_id",)
	search_fields = ("equipo_id", "nombre_equipo", "jefe_equipo_rut__rut", "jefe_equipo_rut__nombre", "jefe_equipo_rut__apellido")
	inlines = [EquipoCalificadorInline]

	def nombre_o_id(self, obj):
		return obj.nombre_equipo if obj.nombre_equipo else f"Equipo #{obj.equipo_id}"
	nombre_o_id.short_description = "Equipo"

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if db_field.name == 'jefe_equipo_rut':
			object_id = request.resolver_match.kwargs.get('object_id')
			if object_id:
				usados_en_otros = EquipoDeTrabajo.objects.exclude(pk=object_id).values_list('jefe_equipo_rut__rut', flat=True)
				qs = JefeEquipo.objects.exclude(rut__in=[r for r in usados_en_otros if r])
			else:
				usados = EquipoDeTrabajo.objects.values_list('jefe_equipo_rut__rut', flat=True)
				qs = JefeEquipo.objects.exclude(rut__in=[r for r in usados if r])
			kwargs['queryset'] = qs
			from django import forms
			from .models import Cuenta
			class NombreJefeChoiceField(forms.ModelChoiceField):
				def label_from_instance(self, obj):
					cuenta = Cuenta.objects.filter(rut=obj.rut).first()
					if cuenta:
						nombre = f"{cuenta.nombre} {cuenta.apellido}".strip()
						return nombre if nombre else obj.rut
					return obj.rut
			kwargs['form_class'] = NombreJefeChoiceField
		return super().formfield_for_foreignkey(db_field, request, **kwargs)

	def jefe_nombre(self, obj):
		jefe = obj.jefe_equipo_rut
		if jefe:
			return f"{getattr(jefe, 'nombre', '')} {getattr(jefe, 'apellido', '')} ({jefe.rut})"
		return "-"
	jefe_nombre.short_description = "Jefe de Equipo"

	def miembros_equipo(self, obj):
		miembros = obj.calificadores.all()
		nombres = [f"{getattr(m, 'nombre', '')} {getattr(m, 'apellido', '')} ({m.rut})" for m in miembros]
		return ", ".join(nombres) if nombres else "-"
	miembros_equipo.short_description = "Miembros del equipo"

	def calificadores_count(self, obj):
		return obj.calificadores.count()
	calificadores_count.short_description = "# Calificadores"


## Modelo Rol eliminado: el rol ahora se deriva automáticamente por RUT en Cuenta


@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
	# Mostrar datos clave; equipo y rol se calculan automáticamente
	list_display = ("cuenta_id", "rut", "rol", "equipo_trabajo", "nombre", "apellido", "edad", "correo", "telefono")
	# Enlace principal de edición
	list_display_links = ("cuenta_id", "rut")
	# Quitar edición en línea: sólo acceder al formulario de detalle
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


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
	list_display = ("empresa_rut", "nombre_empresa", "pais", "tipo_de_empresa", "ingresado_por", "fecha_ingreso")
	search_fields = ("empresa_rut", "nombre_empresa", "pais", "tipo_de_empresa", "ingresado_por__rut")
	readonly_fields = ("ingresado_por_rut", "fecha_ingreso")

	def get_fields(self, request, obj=None):
		base = ["empresa_rut", "nombre_empresa", "pais", "tipo_de_empresa"]
		if obj:
			base += ["ingresado_por", "ingresado_por_rut", "fecha_ingreso"]
		else:
			base += ["ingresado_por"]
		return base

	def save_model(self, request, obj, form, change):
		# El rut de la cuenta se rellena automáticamente en clean()
		obj.save()

