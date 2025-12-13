from rest_framework import serializers
from .models import (
    CalificadorTributario,
    JefeEquipo,
    EquipoDeTrabajo,
    EquipoCalificador,
    Cuenta,
    Empresa,
    CalificacionTributaria,
    CalificacionAprovada,
    CalificacionRechazada
)

# ========================================
# SERIALIZERS PARA AUTENTICACIÓN
# ========================================

class LoginSerializer(serializers.Serializer):
    """
    Serializer para login - Recibe credenciales y devuelve info del usuario
    """
    rut = serializers.CharField(
        max_length=13,
        help_text='RUT del usuario (con o sin formato)'
    )
    contrasena = serializers.CharField(
        write_only=True,  # Solo para escritura, nunca se devuelve
        style={'input_type': 'password'},
        help_text='Contraseña del usuario'
    )
    
    # Campos de respuesta (read_only)
    cuenta_id = serializers.IntegerField(read_only=True)
    nombre = serializers.CharField(read_only=True)
    apellido = serializers.CharField(read_only=True)
    rol = serializers.CharField(read_only=True)
    correo = serializers.EmailField(read_only=True)
    equipo_id = serializers.IntegerField(read_only=True, allow_null=True)
    equipo_nombre = serializers.CharField(read_only=True, allow_null=True)
    
    def validate(self, data):
        """
        Valida las credenciales del usuario
        """
        from .validators import formatear_rut
        
        rut = data.get('rut')
        contrasena = data.get('contrasena')
        
        if not rut or not contrasena:
            raise serializers.ValidationError('RUT y contraseña son obligatorios.')
        
        # Formatear RUT para búsqueda
        try:
            rut_formateado = formatear_rut(rut)
        except:
            raise serializers.ValidationError('Formato de RUT inválido.')
        
        # Buscar usuario
        try:
            cuenta = Cuenta.objects.select_related('equipo_trabajo').get(rut=rut_formateado)
        except Cuenta.DoesNotExist:
            raise serializers.ValidationError('Credenciales inválidas.')
        
        # Validar contraseña (en producción deberías usar hashing)
        if cuenta.contrasena != contrasena:
            raise serializers.ValidationError('Credenciales inválidas.')
        
        # Agregar datos del usuario a la respuesta
        data['cuenta_id'] = cuenta.cuenta_id
        data['nombre'] = cuenta.nombre
        data['apellido'] = cuenta.apellido
        data['rol'] = cuenta.rol
        data['correo'] = cuenta.correo
        data['equipo_id'] = cuenta.equipo_trabajo.equipo_id if cuenta.equipo_trabajo else None
        data['equipo_nombre'] = cuenta.equipo_trabajo.nombre_equipo if cuenta.equipo_trabajo else None
        
        return data


# ========================================
# SERIALIZERS PARA LA APP DEL JEFE
# ========================================

# 1. Serializer para CalificadorTributario
class CalificadorTributarioSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar información de calificadores
    """
    class Meta:
        model = CalificadorTributario
        fields = ['rut', 'fecha_ingreso', 'rol']
        read_only_fields = ['rol']


# 2. Serializer para JefeEquipo
class JefeEquipoSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar información del jefe de equipo
    """
    class Meta:
        model = JefeEquipo
        fields = ['rut', 'fecha_ingreso', 'rol']
        read_only_fields = ['rol']


# 3. Serializer ligero para Cuenta (sin contraseña)
class CuentaLightSerializer(serializers.ModelSerializer):
    """
    Serializer ligero de Cuenta para mostrar en listas
    Excluye la contraseña por seguridad
    """
    equipo_nombre = serializers.CharField(
        source='equipo_trabajo.nombre_equipo',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Cuenta
        fields = [
            'cuenta_id', 'rut', 'rol', 'nombre', 'apellido',
            'telefono', 'correo', 'direccion', 'edad', 'equipo_nombre'
        ]
        read_only_fields = ['cuenta_id', 'rol']


# 4. Serializer completo de Cuenta (para perfil)
class CuentaSerializer(serializers.ModelSerializer):
    """
    Serializer completo de Cuenta para edición de perfil
    NUNCA incluye la contraseña (usar CambiarContrasenaSerializer para eso)
    """
    equipo_nombre = serializers.CharField(
        source='equipo_trabajo.nombre_equipo',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Cuenta
        fields = [
            'cuenta_id', 'rut', 'rol', 'equipo_trabajo',
            'nombre', 'apellido', 'telefono', 'correo',
            'direccion', 'edad', 'equipo_nombre'
        ]
        read_only_fields = ['cuenta_id', 'rol', 'equipo_trabajo']
        # Excluimos completamente la contraseña de este serializer


# 5. Serializer para EquipoCalificador (miembros del equipo)
class EquipoCalificadorSerializer(serializers.ModelSerializer):
    """
    Serializer para la relación entre equipos y calificadores
    """
    calificador_rut = serializers.CharField(source='calificador.rut', read_only=True)
    calificador_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = EquipoCalificador
        fields = ['id', 'equipo', 'calificador', 'calificador_rut', 'calificador_nombre']
    
    def get_calificador_nombre(self, obj):
        try:
            cuenta = Cuenta.objects.get(rut=obj.calificador.rut)
            return f"{cuenta.nombre} {cuenta.apellido}"
        except Cuenta.DoesNotExist:
            return "Sin nombre"


# 6. Serializer para EquipoDeTrabajo (con miembros)
class EquipoDeTrabajoSerializer(serializers.ModelSerializer):
    """
    Serializer completo del equipo con información del jefe y calificadores
    """
    jefe_nombre = serializers.SerializerMethodField()
    calificadores_info = serializers.SerializerMethodField()
    total_miembros = serializers.SerializerMethodField()
    
    class Meta:
        model = EquipoDeTrabajo
        fields = [
            'equipo_id', 'nombre_equipo', 'jefe_equipo_rut',
            'jefe_nombre', 'calificadores_info', 'total_miembros'
        ]
    
    def get_jefe_nombre(self, obj):
        if obj.jefe_equipo_rut:
            try:
                cuenta = Cuenta.objects.get(rut=obj.jefe_equipo_rut.rut)
                return f"{cuenta.nombre} {cuenta.apellido}"
            except Cuenta.DoesNotExist:
                return "Sin nombre"
        return None
    
    def get_calificadores_info(self, obj):
        miembros = EquipoCalificador.objects.filter(equipo=obj).select_related('calificador')
        resultado = []
        for miembro in miembros:
            try:
                cuenta = Cuenta.objects.get(rut=miembro.calificador.rut)
                resultado.append({
                    'rut': miembro.calificador.rut,
                    'nombre': f"{cuenta.nombre} {cuenta.apellido}",
                    'correo': cuenta.correo
                })
            except Cuenta.DoesNotExist:
                resultado.append({
                    'rut': miembro.calificador.rut,
                    'nombre': 'Sin información',
                    'correo': None
                })
        return resultado
    
    def get_total_miembros(self, obj):
        return EquipoCalificador.objects.filter(equipo=obj).count()


# 7. Serializer para Empresa
class EmpresaSerializer(serializers.ModelSerializer):
    """
    Serializer para empresas registradas
    """
    ingresado_por_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Empresa
        fields = [
            'empresa_rut', 'nombre_empresa', 'pais',
            'tipo_de_empresa', 'fecha_ingreso',
            'ingresado_por', 'ingresado_por_rut', 'ingresado_por_nombre'
        ]
        read_only_fields = ['fecha_ingreso', 'ingresado_por_rut']
    
    def get_ingresado_por_nombre(self, obj):
        if obj.ingresado_por:
            return f"{obj.ingresado_por.nombre} {obj.ingresado_por.apellido}"
        return None


# 8. Serializer ligero para CalificacionTributaria (para listas)
class CalificacionTributariaLightSerializer(serializers.ModelSerializer):
    """
    Serializer ligero para mostrar calificaciones en listas/dashboard
    """
    empresa_nombre = serializers.CharField(source='rut_empresa.nombre_empresa', read_only=True)
    calificador_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = CalificacionTributaria
        fields = [
            'calificacion_id', 'nombre_empresa', 'empresa_nombre',
            'anio_tributario', 'puntaje_calificacion',
            'categoria_calificacion', 'nivel_riesgo',
            'estado_calificacion', 'fecha_calculo',
            'calificador_nombre'
        ]
        read_only_fields = [
            'calificacion_id', 'nombre_empresa', 'estado_calificacion', 'fecha_calculo'
        ]
    
    def get_calificador_nombre(self, obj):
        if obj.cuenta_id:
            return f"{obj.cuenta_id.nombre} {obj.cuenta_id.apellido}"
        return None


# 9. Serializer completo para CalificacionTributaria
class CalificacionTributariaSerializer(serializers.ModelSerializer):
    """
    Serializer completo de calificaciones tributarias
    """
    empresa_nombre = serializers.CharField(source='rut_empresa.nombre_empresa', read_only=True)
    empresa_pais = serializers.CharField(source='rut_empresa.pais', read_only=True)
    calificador_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = CalificacionTributaria
        fields = '__all__'
        read_only_fields = [
            'calificacion_id', 'cuenta_id', 'metodo_calificacion',
            'fecha_calculo', 'estado_calificacion', 'nombre_empresa'
        ]
    
    def get_calificador_nombre(self, obj):
        if obj.cuenta_id:
            return f"{obj.cuenta_id.nombre} {obj.cuenta_id.apellido}"
        return None


# 10. Serializer para CalificacionAprovada
class CalificacionAprovadaSerializer(serializers.ModelSerializer):
    """
    Serializer para calificaciones aprobadas
    """
    calificacion_info = CalificacionTributariaLightSerializer(source='calificacion', read_only=True)
    jefe_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = CalificacionAprovada
        fields = [
            'id', 'calificacion', 'calificacion_info',
            'jefe', 'jefe_rut', 'jefe_nombre',
            'observaciones', 'fecha_aprovacion'
        ]
        read_only_fields = ['id', 'jefe_rut', 'fecha_aprovacion']
    
    def get_jefe_nombre(self, obj):
        if obj.jefe:
            return f"{obj.jefe.nombre} {obj.jefe.apellido}"
        return None


# 11. Serializer para CalificacionRechazada
class CalificacionRechazadaSerializer(serializers.ModelSerializer):
    """
    Serializer para calificaciones rechazadas
    """
    calificacion_info = CalificacionTributariaLightSerializer(source='calificacion', read_only=True)
    jefe_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = CalificacionRechazada
        fields = [
            'id', 'calificacion', 'calificacion_info',
            'jefe', 'jefe_rut', 'jefe_nombre',
            'observaciones', 'fecha_rechazo'
        ]
        read_only_fields = ['id', 'jefe_rut', 'fecha_rechazo']
    
    def get_jefe_nombre(self, obj):
        if obj.jefe:
            return f"{obj.jefe.nombre} {obj.jefe.apellido}"
        return None


# ========================================
# SERIALIZERS PARA ESTADÍSTICAS/DASHBOARD
# ========================================

class EstadisticasEquipoSerializer(serializers.Serializer):
    """
    Serializer para estadísticas del equipo (dashboard)
    """
    total_calificaciones = serializers.IntegerField()
    pendientes = serializers.IntegerField()
    aprobadas = serializers.IntegerField()
    rechazadas = serializers.IntegerField()
    por_aprobar = serializers.IntegerField()
    total_empresas = serializers.IntegerField()
    calificaciones_mes_actual = serializers.IntegerField()


class EstadisticasCalificadorSerializer(serializers.Serializer):
    """
    Serializer para estadísticas por calificador
    """
    calificador_rut = serializers.CharField()
    calificador_nombre = serializers.CharField()
    total_calificaciones = serializers.IntegerField()
    aprobadas = serializers.IntegerField()
    rechazadas = serializers.IntegerField()
    pendientes = serializers.IntegerField()