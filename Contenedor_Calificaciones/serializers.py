from rest_framework import serializers
from .models import (
    EquipoDeTrabajo,
    EquipoCalificador,
    Cuenta,
    CalificacionTributaria,
    CalificacionAprovada,
    CalificacionRechazada
)

# ========================================
# SERIALIZERS PARA APP MÓVIL DEL JEFE
# ========================================

# 1. LOGIN - Solo para Jefe de Equipo
class LoginJefeSerializer(serializers.Serializer):
    """
    Login exclusivo para Jefe de Equipo
    POST: {"rut": "12345678-9", "contrasena": "Password123!"}
    """
    rut = serializers.CharField(max_length=13)
    contrasena = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    # Respuesta
    cuenta_id = serializers.IntegerField(read_only=True)
    nombre = serializers.CharField(read_only=True)
    apellido = serializers.CharField(read_only=True)
    correo = serializers.EmailField(read_only=True)
    telefono = serializers.CharField(read_only=True)
    equipo_id = serializers.IntegerField(read_only=True, allow_null=True)
    equipo_nombre = serializers.CharField(read_only=True, allow_null=True)
    
    def validate(self, data):
        from .validators import formatear_rut
        
        rut = data.get('rut')
        contrasena = data.get('contrasena')
        
        if not rut or not contrasena:
            raise serializers.ValidationError('RUT y contraseña son obligatorios.')
        
        try:
            rut_formateado = formatear_rut(rut)
        except:
            raise serializers.ValidationError('Formato de RUT inválido.')
        
        try:
            cuenta = Cuenta.objects.select_related('equipo_trabajo').get(rut=rut_formateado)
        except Cuenta.DoesNotExist:
            raise serializers.ValidationError('Credenciales inválidas.')
        
        # VALIDAR QUE SEA JEFE
        if cuenta.rol != 'Jefe De Equipo':
            raise serializers.ValidationError('Solo los Jefes de Equipo pueden acceder a esta aplicación.')
        
        # Validar contraseña
        if cuenta.contrasena != contrasena:
            raise serializers.ValidationError('Credenciales inválidas.')
        
        # Datos de respuesta
        data['cuenta_id'] = cuenta.cuenta_id
        data['nombre'] = cuenta.nombre
        data['apellido'] = cuenta.apellido
        data['correo'] = cuenta.correo
        data['telefono'] = cuenta.telefono if cuenta.telefono else ''
        data['equipo_id'] = cuenta.equipo_trabajo.equipo_id if cuenta.equipo_trabajo else None
        data['equipo_nombre'] = cuenta.equipo_trabajo.nombre_equipo if cuenta.equipo_trabajo else None
        
        return data


# 2. PERFIL DEL JEFE
class PerfilJefeSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil del jefe
    """
    equipo_nombre = serializers.CharField(source='equipo_trabajo.nombre_equipo', read_only=True, allow_null=True)
    
    class Meta:
        model = Cuenta
        fields = ['cuenta_id', 'rut', 'nombre', 'apellido', 'correo', 'telefono', 'direccion', 'edad', 'equipo_nombre']
        read_only_fields = ['cuenta_id', 'rut', 'equipo_nombre']


# 3. MIEMBROS DEL EQUIPO
class MiembroEquipoSerializer(serializers.Serializer):
    """
    Serializer simplificado para mostrar miembros del equipo
    """
    rut = serializers.CharField()
    nombre_completo = serializers.CharField()
    correo = serializers.EmailField()
    telefono = serializers.CharField(allow_blank=True)
    total_calificaciones = serializers.IntegerField()
    calificaciones_aprobadas = serializers.IntegerField()
    calificaciones_rechazadas = serializers.IntegerField()
    calificaciones_pendientes = serializers.IntegerField()


# 4. CALIFICACIÓN PENDIENTE (Por Aprobar)
class CalificacionPendienteSerializer(serializers.ModelSerializer):
    """
    Serializer para calificaciones pendientes de aprobación
    """
    empresa_rut = serializers.CharField(source='rut_empresa.empresa_rut', read_only=True)
    empresa_nombre = serializers.CharField(source='rut_empresa.nombre_empresa', read_only=True)
    empresa_pais = serializers.CharField(source='rut_empresa.pais', read_only=True)
    calificador_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = CalificacionTributaria
        fields = [
            'calificacion_id', 'empresa_rut', 'empresa_nombre', 'empresa_pais',
            'anio_tributario', 'tipo_calificacion', 'monto_tributario',
            'factor_tributario', 'unidad_valor', 'puntaje_calificacion',
            'categoria_calificacion', 'nivel_riesgo', 'justificacion_resultado',
            'fecha_calculo', 'calificador_nombre'
        ]
    
    def get_calificador_nombre(self, obj):
        if obj.cuenta_id:
            return f"{obj.cuenta_id.nombre} {obj.cuenta_id.apellido}"
        return "Sin asignar"


# 5. CALIFICACIÓN EN HISTORIAL (Aprobada/Rechazada)
class CalificacionHistorialSerializer(serializers.Serializer):
    """
    Serializer para historial de calificaciones (aprobadas y rechazadas)
    """
    calificacion_id = serializers.IntegerField()
    empresa_rut = serializers.CharField()
    empresa_nombre = serializers.CharField()
    empresa_pais = serializers.CharField()
    anio_tributario = serializers.IntegerField()
    tipo_calificacion = serializers.CharField()
    monto_tributario = serializers.FloatField()
    factor_tributario = serializers.FloatField()
    unidad_valor = serializers.CharField()
    puntaje_calificacion = serializers.IntegerField()
    categoria_calificacion = serializers.CharField()
    nivel_riesgo = serializers.CharField()
    estado = serializers.CharField()  # 'aprobado' o 'rechazado'
    fecha_revision = serializers.DateTimeField()
    observaciones = serializers.CharField(allow_blank=True)
    calificador_nombre = serializers.CharField()


# 6. DASHBOARD - Estadísticas Principales
class DashboardSerializer(serializers.Serializer):
    """
    Dashboard con estadísticas completas para la pantalla de inicio
    """
    # Estadísticas generales
    total_pendientes_aprobar = serializers.IntegerField()
    total_aprobadas_hoy = serializers.IntegerField()
    total_rechazadas_hoy = serializers.IntegerField()
    total_pendientes_mes = serializers.IntegerField()
    total_aprobadas_mes = serializers.IntegerField()
    total_rechazadas_mes = serializers.IntegerField()
    total_calificaciones_equipo = serializers.IntegerField()
    
    # Promedios y tendencias
    promedio_puntaje_aprobadas = serializers.FloatField()
    porcentaje_aprobacion = serializers.FloatField()
    
    # Alertas
    calificaciones_alto_riesgo = serializers.IntegerField()
    calificaciones_antiguas = serializers.IntegerField()  # Más de 7 días sin revisar
    
    # Top calificadores
    top_calificador_nombre = serializers.CharField(allow_blank=True)
    top_calificador_aprobadas = serializers.IntegerField()


# 7. ACCIÓN: Aprobar/Rechazar
class AccionCalificacionSerializer(serializers.Serializer):
    """
    Serializer para aprobar o rechazar una calificación
    """
    calificacion_id = serializers.IntegerField()
    jefe_rut = serializers.CharField()
    observaciones = serializers.CharField(required=False, allow_blank=True)
    accion = serializers.ChoiceField(choices=['aprobar', 'rechazar'])
    
    def validate(self, data):
        from .validators import formatear_rut
        
        # Validar que la calificación existe
        try:
            calificacion = CalificacionTributaria.objects.get(calificacion_id=data['calificacion_id'])
        except CalificacionTributaria.DoesNotExist:
            raise serializers.ValidationError('Calificación no encontrada.')
        
        # Validar que esté en estado por_aprobar
        if calificacion.estado_calificacion != 'por_aprobar':
            raise serializers.ValidationError('Esta calificación ya no está pendiente de aprobación.')
        
        # Validar jefe
        try:
            rut_formateado = formatear_rut(data['jefe_rut'])
            jefe = Cuenta.objects.get(rut=rut_formateado, rol='Jefe De Equipo')
            data['jefe'] = jefe
            data['calificacion'] = calificacion
        except Cuenta.DoesNotExist:
            raise serializers.ValidationError('Jefe no encontrado.')
        
        return data