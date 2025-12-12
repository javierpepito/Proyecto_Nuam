from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Empresa, Cuenta, CalificacionTributaria, CalificacionAprovada, CalificacionRechazada, EquipoCalificador
from .forms import CalificacionTributariaForm
from .forms import RegistroCuentaForm
from .validators import validate_rut_chileno, formatear_rut
from django.urls import reverse
import json
from django.db import transaction, connection
import pandas as pd
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from django.db import IntegrityError
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
from .serializers import GroupSerializer, UserSerializer

#Variables constantes para los roles:
ROL_JEFE = 'Jefe De Equipo'
ROL_CALIFICADOR = 'Calificador Tributario'

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

# Vista de perfil para calificador tributario
def perfil_calificador(request):
    if not request.session.get('cuenta_id') or request.session.get('rol') != 'Calificador Tributario':
        return redirect('identificacion')
    from .models import Cuenta
    cuenta = Cuenta.objects.filter(pk=request.session.get('cuenta_id')).first()
    mensaje = None
    if request.method == 'POST' and cuenta:
        correo = request.POST.get('correo', '').strip()
        edad = request.POST.get('edad', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        cambios = False
        if correo and correo != cuenta.correo:
            cuenta.correo = correo
            cambios = True
        if edad != '' and (str(cuenta.edad) != edad):
            try:
                edad_int = int(edad)
                if edad_int >= 0 and edad_int <= 120:
                    cuenta.edad = edad_int
                    cambios = True
                else:
                    mensaje = "La edad debe estar entre 0 y 120."
            except ValueError:
                mensaje = "La edad debe ser un número válido."
        if telefono != cuenta.telefono:
            cuenta.telefono = telefono
            cambios = True
        if cambios and not mensaje:
            cuenta.save()
            mensaje = "Datos actualizados correctamente."
    equipo = cuenta.equipo_trabajo if cuenta else None
    context = {
        'user': cuenta,
        'equipo': equipo,
        'mensaje': mensaje,
    }
    return render(request, 'Contenedor_Calificaciones/calificador_tributario/perfil_calificador.html', context)
# Vista de perfil para jefe de equipo
def perfil_jefe(request):
    if not request.session.get('cuenta_id') or request.session.get('rol') != 'Jefe De Equipo':
        return redirect('identificacion')
    from .models import Cuenta
    cuenta = Cuenta.objects.filter(pk=request.session.get('cuenta_id')).first()
    equipo = cuenta.equipo_trabajo if cuenta else None
    mensaje = None
    if request.method == 'POST' and cuenta:
        correo = request.POST.get('correo', '').strip()
        edad = request.POST.get('edad', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        cambios = False
        if correo and correo != cuenta.correo:
            cuenta.correo = correo
            cambios = True
        if edad != '' and (str(cuenta.edad) != edad):
            try:
                edad_int = int(edad)
                if edad_int >= 0 and edad_int <= 120:
                    cuenta.edad = edad_int
                    cambios = True
                else:
                    mensaje = "La edad debe estar entre 0 y 120."
            except ValueError:
                mensaje = "La edad debe ser un número válido."
        if telefono != cuenta.telefono:
            cuenta.telefono = telefono
            cambios = True
        if cambios and not mensaje:
            cuenta.save()
            mensaje = "Datos actualizados correctamente."
    context = {
        'user': cuenta,
        'equipo': equipo,
        'mensaje': mensaje,
    }
    return render(request, 'Contenedor_Calificaciones/jefe_tributario/perfil_jefe.html', context)

#Vista inicial del calificador tributario
def Inicio_Calificador(request):
    if not request.session.get('cuenta_id') or not request.session.get('rol') == ROL_CALIFICADOR: 
        return redirect('identificacion')
    
    cuenta_id = request.session.get('cuenta_id')
    calificaciones = CalificacionTributaria.objects.filter(
        cuenta_id=cuenta_id,
        estado_calificacion='por_enviar'
    ).order_by('-fecha_calculo')[:5]
    context = {
        'calificaciones': calificaciones,
    }
    return render(request, 'Contenedor_Calificaciones/calificador_tributario/inicio_calificador.html', context)

#Vista inicial del jefe
def Inicio_Jefe(request):
    if not request.session.get('cuenta_id') or not request.session.get('rol') == ROL_JEFE:
        return redirect('identificacion')
    
    jefe = get_object_or_404(Cuenta, pk=request.session.get('cuenta_id'))
    equipo = jefe.equipo_trabajo
    
    # Obtener calificadores del equipo del jefe
    calificadores_equipo = []
    if equipo:
        calificadores_equipo = Cuenta.objects.filter(
            equipo_trabajo=equipo,
            rol=ROL_CALIFICADOR
        ).order_by('nombre', 'apellido')
    
    # Obtener últimas 6 calificaciones por aprobar del equipo
    calificaciones = []
    if equipo:
        cuentas_calificadores = Cuenta.objects.filter(
            equipo_trabajo=equipo,
            rol=ROL_CALIFICADOR
        )
        calificaciones = CalificacionTributaria.objects.filter(
            cuenta_id__in=cuentas_calificadores,
            estado_calificacion='por_aprobar'
        ).select_related('cuenta_id', 'rut_empresa').order_by('-fecha_calculo')[:5]
    
    context = {
        'calificaciones': calificaciones,
        'calificadores_equipo': calificadores_equipo,
        'nombre_equipo': equipo.nombre_equipo if equipo else 'Sin equipo asignado',
    }
    
    return render(request, 'Contenedor_Calificaciones/jefe_tributario/inicio_jefe.html', context)

def identificacion_view(request):
    """Primera etapa: solicita solo el RUT y redirige según corresponda."""
    mensaje = None
    if request.method == 'POST':
        rut_input = request.POST.get('rut', '').strip()
        if rut_input:
            # Validar/formatear si posible
            try:
                validate_rut_chileno(rut_input)
                rut_formateado = formatear_rut(rut_input)
            except ValidationError:
                rut_formateado = rut_input

            # Verifica si el RUT existe en la base de datos de personas autorizadas
            persona = Cuenta.objects.filter(rut=rut_formateado).first()
            if persona:
                # Ya tiene cuenta, va a login
                request.session['rut_identificado'] = rut_formateado
                request.session['nombre_identificado'] = persona.nombre
                request.session['apellido_identificado'] = persona.apellido
                request.session['cuenta_rol'] = persona.rol
                request.session.pop('rut_invalido', None)
                request.session['login_attempts'] = 0
                request.session.pop('login_block_until', None)
                return redirect('login')
            else:
                # Buscar si el rut está autorizado (en CalificadorTributario o JefeEquipo)
                from .models import CalificadorTributario, JefeEquipo
                autorizado = CalificadorTributario.objects.filter(rut=rut_formateado).exists() or JefeEquipo.objects.filter(rut=rut_formateado).exists()
                if autorizado:
                    # No tiene cuenta, va a crear cuenta
                    return redirect(f"{reverse('registro')}?rut={rut_formateado}")
                else:
                    # No está autorizado
                    mensaje = 'El RUT ingresado no está autorizado. Contacte al administrador.'
        else:
            mensaje = 'Debe ingresar un RUT.'
    return render(request, 'Contenedor_Calificaciones/identificacion.html', {'mensaje': mensaje})


def login_view(request):
    """Segunda etapa: ingreso de contraseña con límite de 3 intentos y bloqueo 10 minutos."""
    rut_identificado = request.session.get('rut_identificado')
    if not rut_identificado:
        return redirect('identificacion')

    rut_invalido = request.session.get('rut_invalido', False)
    nombre_identificado = request.session.get('nombre_identificado')
    apellido_identificado = request.session.get('apellido_identificado')
    error = None
    attempts = request.session.get('login_attempts', 0)
    block_until = request.session.get('login_block_until')  # epoch seconds
    now_ts = timezone.now().timestamp()
    blocked = False
    remaining_seconds = 0

    # Revisar si bloqueo activo
    if block_until and now_ts < block_until:
        blocked = True
        remaining_seconds = int(block_until - now_ts)
    elif block_until and now_ts >= block_until:
        # Bloqueo expirado: resetear
        attempts = 0
        request.session['login_attempts'] = 0
        request.session.pop('login_block_until', None)

    cuenta = None
    if not rut_invalido:
        cuenta = Cuenta.objects.filter(rut=rut_identificado).first()
        if not cuenta:
            rut_invalido = True  # Inconsistencia: marcar
            request.session['rut_invalido'] = True

    if request.method == 'POST' and not rut_invalido and not blocked:
        contrasena = request.POST.get('contrasena', '')
        if contrasena:
            if cuenta and cuenta.contrasena == contrasena:
                # Login correcto
                request.session['cuenta_id'] = cuenta.pk
                request.session['rol'] = cuenta.rol
                request.session['login_attempts'] = 0
                request.session.pop('login_block_until', None)
                rol_identificado = request.session.get('rol')

                if rol_identificado == 'Jefe De Equipo':
                    return redirect('Inicio_Jefe')
                elif rol_identificado == 'Calificador Tributario':
                    return redirect('Inicio_Calificador') 
                else:
                    error = 'No rol asignado'
                
            else:
                attempts += 1
                request.session['login_attempts'] = attempts
                if attempts >= 3:
                    # Bloquear por 10 minutos
                    block_until = now_ts + (10 * 60)
                    request.session['login_block_until'] = block_until
                    blocked = True
                    remaining_seconds = int(block_until - now_ts)
                else:
                    error = 'Contraseña incorrecta.'
        else:
            error = 'Debe ingresar la contraseña.'
    elif request.method == 'POST' and (rut_invalido or blocked):
        # Ignorar POST si RUT inválido o bloqueado
        pass

    attempts_left = max(0, 3 - attempts) if not blocked else 0

    context = {
        'error': error,
        'rut': rut_identificado,
        'nombre': nombre_identificado,
        'apellido': apellido_identificado,
        'rut_invalido': rut_invalido,
        'blocked': blocked,
        'remaining_seconds': remaining_seconds,
        'attempts_left': attempts_left,
    }
    return render(request, 'Contenedor_Calificaciones/login.html', context)

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ["empresa_rut", "nombre_empresa", "pais", "tipo_de_empresa"]

    def clean_nombre_empresa(self):
        nombre = self.cleaned_data.get("nombre_empresa", "")
        return " ".join(p.capitalize() for p in nombre.strip().split())


def registrar_empresa(request):
    # Se asume que el ID de la cuenta activa está en session bajo 'cuenta_id'
    cuenta_id = request.session.get('cuenta_id')
    if not cuenta_id:
        return redirect('identificacion')
    cuenta = get_object_or_404(Cuenta, pk=cuenta_id) if cuenta_id else None

    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save(commit=False)
            if not cuenta:
                form.add_error(None, 'No hay una cuenta activa en la sesión.')
            else:
                empresa.ingresado_por = cuenta
                empresa.save()
                return redirect('lista_empresas')
    else:
        form = EmpresaForm()
    return render(request, 'Contenedor_Calificaciones/calificador_tributario/registrar_empresa.html', {"form": form})


def lista_empresas(request):
    if not request.session.get('cuenta_id'):
        return redirect('identificacion')
    empresas = Empresa.objects.select_related('ingresado_por').all().order_by('-fecha_ingreso')
    return render(request, 'Contenedor_Calificaciones/calificador_tributario/lista_empresas.html', {"empresas": empresas})


def logout_view(request):
    """Cierra sesión limpiando la información y redirige a identificación."""
    # El flush elimina la sesión completa (incluye intentos y bloqueos)
    try:
        request.session.flush()
    except Exception:
        # Fallback si flush falla por alguna razón
        for key in [
            'cuenta_id','rut_identificado','nombre_identificado','rut_invalido',
            'login_attempts','login_block_until'
        ]:
            request.session.pop(key, None)
    return redirect('identificacion')

#Vista para agregar calificacion tributaria
def agregar_calificacion(request):
    if not request.session.get('cuenta_id') or not request.session.get('rol') == ROL_CALIFICADOR: 
        return redirect('identificacion')
    
    cuenta_id = request.session.get('cuenta_id')
    try:
        cuenta = Cuenta.objects.get(pk=cuenta_id)
    except Cuenta.DoesNotExist:
        messages.error(request, 'Sesión inválida. Por favor, inicie sesión nuevamente.')
        return redirect('identificacion')
    
    if request.method == 'POST':
        # Determinar qué botón fue presionado
        accion = request.POST.get('accion')
        
        # Si presionó cancelar, redirigir sin procesar
        if accion == 'cancelar':
            messages.info(request, 'Operación cancelada.')
            return redirect('Inicio_Calificador')
        
        form = CalificacionTributariaForm(request.POST)
        
        if form.is_valid():
            # Obtener el RUT y nombre validados del formulario
            rut_empresa = form.cleaned_data['rut_empresa']
            nombre_empresa = form.cleaned_data['nombre_empresa']
            
            # Buscar la empresa (ya validamos que existe y coincide en clean())
            try:
                empresa = Empresa.objects.get(empresa_rut=rut_empresa)
            except Empresa.DoesNotExist:
                # Este caso no debería ocurrir por la validación, pero por seguridad:
                messages.error(request, f'La empresa con RUT {rut_empresa} no existe. Por favor regístrela primero.')
                context = {'form': form}
                return render(request, 'Contenedor_Calificaciones/calificador_tributario/calificacion_manual.html', context)
            
            # Crear el objeto sin guardar aún
            calificacion = form.save(commit=False)
            
            # CRÍTICO: Asignar la FK y el nombre ANTES de cualquier validación o guardado
            calificacion.rut_empresa = empresa
            # Usar el nombre de la empresa tal como está en la BD (capitalizado correctamente)
            calificacion.nombre_empresa = empresa.nombre_empresa 
            calificacion.cuenta_id = cuenta
            calificacion.metodo_calificacion = 'manual'
            
            # Determinar el estado según el botón presionado
            if accion == 'por_enviar':
                calificacion.estado_calificacion = 'por_enviar'
                mensaje = 'Calificación guardada como Por Enviar exitosamente.'
            elif accion == 'enviar':
                calificacion.estado_calificacion = 'por_aprobar'
                mensaje = 'Calificación enviada para aprobación exitosamente.'
            else:
                calificacion.estado_calificacion = 'pendiente'
                mensaje = 'Calificación guardada exitosamente.'
            
            try:
                # Guardar en la base de datos
                calificacion.save()
                messages.success(request, mensaje)
                return redirect('agregar_calificacion')
            except Exception as e:
                messages.error(request, f'Error al guardar la calificación: {str(e)}')
        
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
    
    else:
        # GET: Mostrar formulario vacío
        form = CalificacionTributariaForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'Contenedor_Calificaciones/calificador_tributario/calificacion_manual.html', context)

#Vista para agregar calificacion tributaria mediante archivo masivo
def carga_masiva_view(request):
    """
    Vista para carga masiva de calificaciones desde archivo Excel.
    Muestra vista previa de los datos con validaciones.
    """
    if not request.session.get('cuenta_id') or not request.session.get('rol') == ROL_CALIFICADOR:
        return redirect('identificacion')
    
    datos_procesados = []
    errores_globales = []
    archivo_nombre = None
    
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        archivo_nombre = archivo.name
        
        # Validar extensión del archivo
        if not archivo.name.endswith(('.xlsx', '.xls')):
            errores_globales.append('El archivo debe ser formato Excel (. xlsx o .xls)')
        else:
            try:
                # Leer el archivo Excel
                df = pd.read_excel(archivo, engine='openpyxl')
                
                # Validar que no esté vacío
                if df.empty:
                    errores_globales.append('El archivo Excel está vacío.')
                else:
                    # Normalizar nombres de columnas (quitar espacios extra)
                    df.columns = df.columns.str.strip()
                    
                    # Función helper para encontrar columna (tolera variaciones de tildes)
                    def encontrar_columna(df, posibles_nombres):
                        for nombre in posibles_nombres:
                            if nombre in df.columns:
                                return nombre
                        return None
                    
                    # Mapeo flexible de columnas
                    col_rut = encontrar_columna(df, ['RUT de la Empresa'])
                    col_nombre = encontrar_columna(df, ['Nombre de la Empresa'])
                    col_anio = encontrar_columna(df, ['Año Tributario'])
                    col_tipo = encontrar_columna(df, ['Tipo de Calificación', 'Tipo de Calificacion'])
                    col_monto = encontrar_columna(df, ['Monto Tributario'])
                    col_factor = encontrar_columna(df, ['Factor Tributario'])
                    col_unidad = encontrar_columna(df, ['Unidad de Valor'])
                    col_puntaje = encontrar_columna(df, ['Puntaje de Calificación', 'Puntaje de Calificacion'])
                    col_categoria = encontrar_columna(df, ['Categoría de la Calificación', 'Categoria de la Calificación', 'Categoría de la Calificacion', 'Categoria de la Calificacion'])
                    col_riesgo = encontrar_columna(df, ['Nivel de Riesgo'])
                    col_justificacion = encontrar_columna(df, ['Justificación del resultado (Observaciones)', 'Justificacion del resultado (Observaciones)'])
                    
                    # Validar que existan todas las columnas necesarias
                    columnas_faltantes = []
                    if not col_rut: columnas_faltantes.append('RUT de la Empresa')
                    if not col_nombre: columnas_faltantes.append('Nombre de la Empresa')
                    if not col_anio: columnas_faltantes.append('Año Tributario')
                    if not col_tipo: columnas_faltantes.append('Tipo de Calificación')
                    if not col_monto: columnas_faltantes.append('Monto Tributario')
                    if not col_factor: columnas_faltantes.append('Factor Tributario')
                    if not col_unidad: columnas_faltantes.append('Unidad de Valor')
                    if not col_puntaje: columnas_faltantes.append('Puntaje de Calificación')
                    if not col_categoria: columnas_faltantes.append('Categoría de la Calificación')
                    if not col_riesgo: columnas_faltantes.append('Nivel de Riesgo')
                    if not col_justificacion: columnas_faltantes.append('Justificación del resultado (Observaciones)')
                    
                    if columnas_faltantes:
                        errores_globales.append(f"Faltan columnas en el Excel: {', '.join(columnas_faltantes)}")
                    else:
                        # Procesar cada fila (máximo 10)
                        filas_procesadas = 0
                        
                        for index, row in df.iterrows():
                            # Saltar filas vacías
                            if pd.isna(row[col_rut]) or str(row[col_rut]).strip() == '':
                                continue
                            
                            if filas_procesadas >= 10:
                                errores_globales.append('⚠️ Se permiten máximo 10 calificaciones por archivo.  Las filas adicionales fueron ignoradas.')
                                break
                            
                            filas_procesadas += 1
                            errores_fila = []
                            
                            # Validar RUT empresa (debe existir en BD)
                            rut_empresa_valor = str(row[col_rut]).strip()
                            nombre_empresa_excel = str(row[col_nombre]).strip() if pd.notna(row[col_nombre]) else ''

                            try:
                                validate_rut_chileno(rut_empresa_valor)
                                rut_formateado = formatear_rut(rut_empresa_valor)
                                empresa = Empresa.objects.filter(empresa_rut=rut_formateado).first()
                                
                                if not empresa:
                                    errores_fila.append(f'Empresa con RUT {rut_formateado} no está registrada.')
                                else:
                                    # Validar que el nombre coincida (normalizar para comparación)
                                    nombre_bd = empresa.nombre_empresa.strip().lower()
                                    nombre_excel = nombre_empresa_excel.strip().lower()
                                    
                                    # Comparación exacta (sin distinguir mayúsculas/minúsculas)
                                    if nombre_bd != nombre_excel:
                                        errores_fila.append(
                                            f'El nombre "{nombre_empresa_excel}" no coincide con la empresa registrada para el RUT {rut_formateado}.'
                                        )
                                        empresa = None  # Marcar como inválida
                                        
                            except ValidationError as e:
                                errores_fila.append(f'RUT inválido: {rut_empresa_valor}')
                                rut_formateado = rut_empresa_valor
                                empresa = None
                            
                            # Validar año tributario
                            try:
                                anio = int(row[col_anio])
                                if anio < 1900 or anio > timezone.now().year:
                                    errores_fila.append(f'Año tributario {anio} fuera de rango (1900-{timezone.now().year})')
                            except (ValueError, TypeError):
                                errores_fila.append(f'Año tributario inválido: {row[col_anio]}')
                                anio = None
                            
                            # Validar monto tributario
                            try:
                                monto = float(row[col_monto])
                                if monto < 0:
                                    errores_fila.append('Monto tributario no puede ser negativo')
                            except (ValueError, TypeError):
                                errores_fila.append(f'Monto tributario inválido: {row[col_monto]}')
                                monto = None
                            
                            # Validar factor tributario
                            try:
                                factor = float(row[col_factor])
                                if factor < 0:
                                    errores_fila.append('Factor tributario no puede ser negativo')
                                elif factor > 1:
                                    errores_fila.append('Factor tributario debe ser un valor entre 0 y 1 (Ej: 0.5 para 50%)')
                            except (ValueError, TypeError):
                                errores_fila.append(f'Factor tributario inválido: {row[col_factor]}')
                                factor = None
                            
                            # Validar puntaje (0-100)
                            try:
                                puntaje = int(row[col_puntaje])
                                if puntaje < 0 or puntaje > 100:
                                    errores_fila.append('Puntaje debe estar entre 0 y 100')
                            except (ValueError, TypeError):
                                errores_fila.append(f'Puntaje inválido: {row[col_puntaje]}')
                                puntaje = None
                            
                            # Validar categoría
                            categoria_map = {
                                'A': 'alto', 'B': 'medio', 'C': 'bajo',  
                                'a': 'alto', 'b': 'medio', 'c': 'bajo',  
                                'bajo': 'bajo', 'medio': 'medio', 'alto': 'alto',
                                'BAJO': 'bajo', 'MEDIO': 'medio', 'ALTO': 'alto',
                                'Bajo': 'bajo', 'Medio': 'medio', 'Alto': 'alto'
                            }
                            categoria_valor = str(row[col_categoria]).strip()
                            if categoria_valor not in categoria_map:
                                errores_fila.append(f'Categoría inválida: {categoria_valor}. Debe ser: A, B, C o Bajo, Medio, Alto')
                                categoria = None
                            else:
                                categoria = categoria_map[categoria_valor]
                            
                            # Validar nivel de riesgo
                            riesgo_map = {
                                'bajo': 'bajo', 'medio': 'medio', 'alto': 'alto', 'critico': 'critico', 'crítico': 'critico',
                                'BAJO': 'bajo', 'MEDIO': 'medio', 'ALTO': 'alto', 'CRITICO': 'critico', 'CRÍTICO': 'critico',
                                'Bajo': 'bajo', 'Medio': 'medio', 'Alto': 'alto', 'Critico': 'critico', 'Crítico': 'critico'
                            }
                            riesgo_valor = str(row[col_riesgo]).strip()
                            if riesgo_valor not in riesgo_map:
                                errores_fila.append(f'Nivel de riesgo inválido: {riesgo_valor}.  Debe ser: Bajo, Medio, Alto o Crítico')
                                riesgo = None
                            else:
                                riesgo = riesgo_map[riesgo_valor]
                            
                            # Agregar datos procesados
                            datos_procesados.append({
                                'fila': index + 2,  # +2 porque Excel empieza en 1 y tiene header
                                'rut_empresa': rut_formateado if rut_formateado else rut_empresa_valor,
                                'nombre_empresa': str(row[col_nombre]).strip() if pd.notna(row[col_nombre]) else '',
                                'anio_tributario': anio,
                                'tipo_calificacion': str(row[col_tipo]).strip() if pd.notna(row[col_tipo]) else '',
                                'monto_tributario': monto,
                                'factor_tributario': factor,
                                'unidad_valor': str(row[col_unidad]).strip() if pd.notna(row[col_unidad]) else '',
                                'puntaje_calificacion': puntaje,
                                'categoria_calificacion': categoria,
                                'nivel_riesgo': riesgo,
                                'justificacion_resultado': str(row[col_justificacion]).strip() if pd.notna(row[col_justificacion]) else '',
                                'errores': errores_fila,
                                'valido': len(errores_fila) == 0
                            })
                        
                        if filas_procesadas == 0:
                            errores_globales.append('No se encontraron filas válidas con datos en el archivo.')
                            
            except Exception as e:
                errores_globales.append(f'Error al procesar el archivo: {str(e)}')
    
    # Serializar datos válidos para pasarlos a la siguiente vista
    datos_validos = [d for d in datos_procesados if d['valido']]
    datos_json = json.dumps(datos_validos) if datos_validos else ''

    context = {
        'datos_procesados': datos_procesados,
        'errores_globales': errores_globales,
        'archivo_nombre': archivo_nombre,
        'total_registros': len(datos_procesados),
        'registros_validos': sum(1 for d in datos_procesados if d['valido']),
        'registros_con_errores': sum(1 for d in datos_procesados if not d['valido']),
        'datos_json': datos_json,  # ← NUEVO
    }
    
    return render(request, 'Contenedor_Calificaciones/calificador_tributario/carga_masiva.html', context)

#Vista para crear cuenta
def registro_view(request):
    """Vista para registro de nueva cuenta"""
    if request.method == 'POST':
        form = RegistroCuentaForm(request.POST)
        if form.is_valid():
            try:
                cuenta = form.save()
                messages.success(request, '¡Cuenta creada exitosamente! Ya puedes iniciar sesión.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'Error al crear la cuenta: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
    else:
        form = RegistroCuentaForm()
    
    return render(request, 'Contenedor_Calificaciones/registro.html', {'form': form})

# Vista para mostrar las calificaciones del usuario en estado "por aprobar"
def tus_calificaciones(request):
    if not request.session.get('cuenta_id') or not request.session.get('rol') == ROL_CALIFICADOR:
        return redirect('identificacion')
    
    cuenta_id = request.session.get('cuenta_id')
    try:
        cuenta = Cuenta.objects.get(pk=cuenta_id)
    except Cuenta.DoesNotExist:
        messages.error(request, 'Sesión inválida. Por favor, inicie sesión nuevamente.')
        return redirect('identificacion')
    
    # Obtener parámetros de filtro
    rut = request.GET.get('rut', '').strip()
    nombre_empresa = request.GET.get('nombre_empresa', '').strip()
    anio = request.GET.get('anio', '').strip()
    estado = request.GET.get('estado', '').strip()  # Nuevo filtro por estado
    page_size = int(request.GET.get('page_size', 10))
    
    # Filtrar calificaciones - ahora incluye por_aprobar, aprobado y rechazado
    calificaciones_qs = CalificacionTributaria.objects.filter(
        cuenta_id=cuenta,
        estado_calificacion__in=['por_aprobar', 'aprobado', 'rechazado']
    ).select_related('rut_empresa').prefetch_related('aprobacion', 'rechazo').order_by('-fecha_calculo')
    
    if rut:
        calificaciones_qs = calificaciones_qs.filter(rut_empresa__empresa_rut__icontains=rut)
    
    if nombre_empresa:
        calificaciones_qs = calificaciones_qs.filter(rut_empresa__nombre_empresa__icontains=nombre_empresa)
    
    if anio:
        calificaciones_qs = calificaciones_qs.filter(anio_tributario=anio)
    
    # Filtrar por estado si se proporciona
    if estado:
        calificaciones_qs = calificaciones_qs.filter(estado_calificacion=estado)
    
    # Paginación
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(calificaciones_qs, page_size)
    page = request.GET.get('page')
    
    try:
        calificaciones = paginator.page(page)
    except PageNotAnInteger:
        calificaciones = paginator.page(1)
    except EmptyPage:
        calificaciones = paginator.page(paginator.num_pages)
    
    # Agregar observaciones a cada calificación
    for calificacion in calificaciones:
        calificacion.observacion_jefe = None
        calificacion.fecha_revision = None
        calificacion.jefe_revisor = None
        
        if calificacion.estado_calificacion == 'aprobado':
            aprobacion = calificacion.aprobacion.first()
            if aprobacion:
                calificacion.observacion_jefe = aprobacion.observaciones
                calificacion.fecha_revision = aprobacion.fecha_aprovacion
                calificacion.jefe_revisor = aprobacion.jefe_rut
        elif calificacion.estado_calificacion == 'rechazado':
            rechazo = calificacion.rechazo.first()
            if rechazo:
                calificacion.observacion_jefe = rechazo.observaciones
                calificacion.fecha_revision = rechazo.fecha_rechazo
                calificacion.jefe_revisor = rechazo.jefe_rut
    
    context = {
        'calificaciones': calificaciones,
        'total_calificaciones': paginator.count,
        'page_obj': calificaciones,
        'paginator': paginator,
        'page_size': page_size,
        'estado_filtro': estado,  # Para mantener el filtro activo
    }
    
    return render(request, 'Contenedor_Calificaciones/calificador_tributario/tus_calificaciones.html', context)

# Vista para mostrar las calificaciones del usuario en estado "por_enviar"
def calificaciones_pendientes(request):
    """
    Vista para mostrar las calificaciones del usuario en estado 'por_enviar'
    """
    if not request.session.get('cuenta_id') or not request.session.get('rol') == ROL_CALIFICADOR:
        return redirect('identificacion')
    
    cuenta_id = request.session.get('cuenta_id')
    try:
        cuenta = Cuenta.objects.get(pk=cuenta_id)
    except Cuenta.DoesNotExist:
        messages.error(request, 'Sesión inválida. Por favor, inicie sesión nuevamente.')
        return redirect('identificacion')
    
    # Obtener parámetros de filtro
    rut = request.GET.get('rut', '').strip()
    nombre_empresa = request.GET.get('nombre_empresa', '').strip()
    anio = request.GET.get('anio', '').strip()
    page_size = int(request.GET.get('page_size', 10))
    
    # Obtener las calificaciones del usuario en estado 'por_enviar'
    calificaciones_qs = CalificacionTributaria.objects.filter(
        cuenta_id=cuenta,
        estado_calificacion='por_enviar'
    ).select_related('rut_empresa').order_by('-fecha_calculo')
    
    if rut:
        calificaciones_qs = calificaciones_qs.filter(rut_empresa__empresa_rut__icontains=rut)
    
    if nombre_empresa:
        calificaciones_qs = calificaciones_qs.filter(rut_empresa__nombre_empresa__icontains=nombre_empresa)
    
    if anio:
        calificaciones_qs = calificaciones_qs.filter(anio_tributario=anio)
    
    # Paginación
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(calificaciones_qs, page_size)
    page = request.GET.get('page')
    
    try:
        calificaciones = paginator.page(page)
    except PageNotAnInteger:
        calificaciones = paginator.page(1)
    except EmptyPage:
        calificaciones = paginator.page(paginator.num_pages)
    
    context = {
        'calificaciones': calificaciones,
        'total_calificaciones': paginator.count,
        'page_obj': calificaciones,
        'paginator': paginator,
        'page_size': page_size,
    }
    
    return render(request, 'Contenedor_Calificaciones/calificador_tributario/calificaciones_pendientes.html', context)


#Vista para editar una calificación por enviar
def editar_calificacion_pendiente(request, calificacion_id):
    """
    Vista para editar una calificación en estado 'por_enviar'
    """
    if not request.session.get('cuenta_id') or not request.session.get('rol') == ROL_CALIFICADOR:
        return redirect('identificacion')
    
    cuenta_id = request.session.get('cuenta_id')
    try:
        cuenta = Cuenta.objects.get(pk=cuenta_id)
    except Cuenta.DoesNotExist:
        messages.error(request, 'Sesión inválida. Por favor, inicie sesión nuevamente.')
        return redirect('identificacion')
    
    # Obtener la calificación y verificar que pertenezca al usuario y esté pendiente
    calificacion = get_object_or_404(CalificacionTributaria, pk=calificacion_id)
    
    # Verificar que la calificación pertenece al usuario
    if calificacion.cuenta_id != cuenta:
        messages.error(request, 'No tienes permisos para editar esta calificación.')
        return redirect('calificaciones_pendientes')
    
    # Verificar que la calificación esté en estado por enviar
    if calificacion.estado_calificacion != 'por_enviar':
        messages.error(request, 'Solo puedes editar calificaciones en estado Por Enviar.')
        return redirect('calificaciones_pendientes')
    
    if request.method == 'POST':
        form = CalificacionTributariaForm(request.POST, instance=calificacion)
        
        if form.is_valid():
            try:
                # Obtener RUT de empresa del formulario
                rut_empresa = form.cleaned_data['rut_empresa']
                empresa = Empresa.objects.get(empresa_rut=rut_empresa)
                
                # Guardar la calificación actualizada
                calificacion_actualizada = form.save(commit=False)
                calificacion_actualizada.rut_empresa = empresa
                calificacion_actualizada.nombre_empresa = empresa.nombre_empresa
                calificacion_actualizada.cuenta_id = cuenta
                calificacion_actualizada.metodo_calificacion = 'manual'
                calificacion_actualizada.estado_calificacion = 'por_enviar'
                calificacion_actualizada.save()
                
                messages.success(request, f'Calificación #{calificacion_id} actualizada exitosamente.')
                return redirect('calificaciones_pendientes')
                
            except Empresa.DoesNotExist:
                messages.error(request, 'La empresa especificada no existe.')
            except Exception as e:
                messages.error(request, f'Error al actualizar la calificación: {str(e)}')
    else:
        # Prellenar el formulario con los datos existentes
        initial_data = {
            'rut_empresa': calificacion.rut_empresa.empresa_rut,
            'nombre_empresa': calificacion.nombre_empresa,
        }
        form = CalificacionTributariaForm(instance=calificacion, initial=initial_data)
    
    context = {
        'form': form,
        'calificacion': calificacion,
        'editar': True,
    }
    
    return render(request, 'Contenedor_Calificaciones/calificador_tributario/editar_calificacion.html', context)


#Vista para eliminar una calificación pendiente (soft delete)
def eliminar_calificacion_pendiente(request, calificacion_id):
    """
    Vista para realizar soft delete de una calificación en estado 'por_enviar'.
    Cambia el estado a 'eliminado' sin borrar el registro de la BD.
    """
    if not request.session.get('cuenta_id') or not request.session.get('rol') == ROL_CALIFICADOR:
        return redirect('identificacion')
    
    cuenta_id = request.session.get('cuenta_id')
    try:
        cuenta = Cuenta.objects.get(pk=cuenta_id)
    except Cuenta.DoesNotExist:
        messages.error(request, 'Sesión inválida. Por favor, inicie sesión nuevamente.')
        return redirect('identificacion')
    
    # Obtener la calificación
    calificacion = get_object_or_404(CalificacionTributaria, pk=calificacion_id)
    
    # Verificar que la calificación pertenece al usuario
    if calificacion.cuenta_id != cuenta:
        messages.error(request, 'No tienes permisos para eliminar esta calificación.')
        return redirect('calificaciones_pendientes')
    
    # Verificar que la calificación esté en estado por enviar
    if calificacion.estado_calificacion != 'por_enviar':
        messages.error(request, 'Solo puedes eliminar calificaciones en estado Por Enviar.')
        return redirect('calificaciones_pendientes')
    
    # Guardar información para el mensaje
    nombre_empresa = calificacion.nombre_empresa
    
    try:
        # Soft delete: cambiar estado a 'eliminado' en lugar de borrar
        calificacion.estado_calificacion = 'eliminado'
        calificacion.save()
        messages.success(request, f'Calificación de {nombre_empresa} eliminada exitosamente.')
    except Exception as e:
        messages.error(request, f'Error al eliminar la calificación: {str(e)}')
    
    return redirect('calificaciones_pendientes')


#Vista para enviar una calificación pendiente para aprobación
def enviar_calificacion_pendiente(request, calificacion_id):
    """
    Vista para cambiar el estado de una calificación de 'por_enviar' a 'por_aprobar'
    """
    if not request.session.get('cuenta_id') or not request.session.get('rol') == ROL_CALIFICADOR:
        return redirect('identificacion')
    
    cuenta_id = request.session.get('cuenta_id')
    try:
        cuenta = Cuenta.objects.get(pk=cuenta_id)
    except Cuenta.DoesNotExist:
        messages.error(request, 'Sesión inválida. Por favor, inicie sesión nuevamente.')
        return redirect('identificacion')
    
    # Obtener la calificación
    calificacion = get_object_or_404(CalificacionTributaria, pk=calificacion_id)
    
    # Verificar que la calificación pertenece al usuario
    if calificacion.cuenta_id != cuenta:
        messages.error(request, 'No tienes permisos para enviar esta calificación.')
        return redirect('calificaciones_pendientes')
    
    # Verificar que la calificación esté en estado por enviar
    if calificacion.estado_calificacion != 'por_enviar':
        messages.error(request, 'Solo puedes enviar calificaciones en estado Por Enviar.')
        return redirect('calificaciones_pendientes')
    
    try:
        # Cambiar el estado a 'por_aprobar'
        calificacion.estado_calificacion = 'por_aprobar'
        calificacion.save()
        messages.success(request, f'Calificación de {calificacion.nombre_empresa} enviada para aprobación exitosamente.')
    except Exception as e:
        messages.error(request, f'Error al enviar la calificación: {str(e)}')
    
    return redirect('calificaciones_pendientes')


# Vista para jefes: ver calificaciones por aprobar de su equipo
def calificaciones_pendientes_jefe(request):
    if not request.session.get('cuenta_id') or request.session.get('rol') != ROL_JEFE:
        return redirect('identificacion')

    jefe = get_object_or_404(Cuenta, pk=request.session.get('cuenta_id'))
    equipo = jefe.equipo_trabajo
    if not equipo:
        messages.info(request, 'No tienes un equipo asignado actualmente.')
        return render(request, 'Contenedor_Calificaciones/jefe_tributario/calificaciones_pendientes_jefe.html', {
            'calificaciones': [],
            'total_calificaciones': 0,
        })

    # Cuentas de calificadores en el equipo del jefe
    cuentas_calificadores = Cuenta.objects.filter(equipo_trabajo=equipo, rol=ROL_CALIFICADOR).order_by('nombre', 'apellido')

    # Filtro por calificador (opcional)
    calificador_id = request.GET.get('calificador_id')
    # Filtro por RUT de empresa (opcional)
    rut_empresa = request.GET.get('rut_empresa')
    
    try:
        page_size = int(request.GET.get('page_size', 10))
    except ValueError:
        page_size = 10
    if page_size not in [10,20,30,40,50]:
        page_size = 10

    base_qs = CalificacionTributaria.objects.filter(
        cuenta_id__in=cuentas_calificadores,
        estado_calificacion='por_aprobar'
    )
    if calificador_id:
        try:
            base_qs = base_qs.filter(cuenta_id_id=int(calificador_id))
        except ValueError:
            pass
    
    if rut_empresa:
        base_qs = base_qs.filter(rut_empresa__empresa_rut__icontains=rut_empresa)

    calificaciones_qs = base_qs.select_related('cuenta_id', 'rut_empresa').order_by('-fecha_calculo')

    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(calificaciones_qs, page_size)
    page = request.GET.get('page')
    try:
        calificaciones = paginator.page(page)
    except PageNotAnInteger:
        calificaciones = paginator.page(1)
    except EmptyPage:
        calificaciones = paginator.page(paginator.num_pages)

    context = {
        'calificaciones': calificaciones,
        'total_calificaciones': paginator.count,
        'calificadores_equipo': cuentas_calificadores,
        'calificador_seleccionado': calificador_id,
        'rut_empresa_filtro': rut_empresa,
        'page_size': page_size,
        'page_obj': calificaciones,
        'paginator': paginator,
    }
    return render(request, 'Contenedor_Calificaciones/jefe_tributario/calificaciones_pendientes_jefe.html', context)


# Vista para jefes: ver calificaciones aprobadas de su equipo
def calificaciones_aprobadas_jefe(request):
    if not request.session.get('cuenta_id') or request.session.get('rol') != ROL_JEFE:
        return redirect('identificacion')

    jefe = get_object_or_404(Cuenta, pk=request.session.get('cuenta_id'))

    # Buscar todas las calificaciones aprobadas por este jefe (sin importar equipo actual)
    aprobadas_ids = CalificacionAprovada.objects.filter(jefe=jefe).values_list('calificacion_id', flat=True)
    base_qs = CalificacionTributaria.objects.filter(
        pk__in=aprobadas_ids,
        estado_calificacion='aprobado'
    )

    # Calificadores únicos de esas calificaciones
    calificadores_ids = base_qs.values_list('cuenta_id', flat=True).distinct()
    calificadores_equipo = list(Cuenta.objects.filter(pk__in=calificadores_ids).order_by('nombre', 'apellido'))

    calificador_id = request.GET.get('calificador_id')
    try:
        page_size = int(request.GET.get('page_size', 10))
    except ValueError:
        page_size = 10
    if page_size not in [10,20,30,40,50]:
        page_size = 10

    if calificador_id:
        try:
            base_qs = base_qs.filter(cuenta_id_id=int(calificador_id))
        except ValueError:
            pass

    calificaciones_qs = base_qs.select_related('cuenta_id', 'rut_empresa').order_by('-fecha_calculo')

    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(calificaciones_qs, page_size)
    page = request.GET.get('page')
    try:
        calificaciones = paginator.page(page)
    except PageNotAnInteger:
        calificaciones = paginator.page(1)
    except EmptyPage:
        calificaciones = paginator.page(paginator.num_pages)

    context = {
        'calificaciones': calificaciones,
        'total_calificaciones': paginator.count,
        'calificadores_equipo': calificadores_equipo,
        'calificador_seleccionado': calificador_id,
        'page_size': page_size,
        'page_obj': calificaciones,
        'paginator': paginator,
    }
    return render(request, 'Contenedor_Calificaciones/jefe_tributario/calificaciones_aprobadas.html', context)


# Vista para jefes: ver calificaciones rechazadas de su equipo
def calificaciones_rechazadas_jefe(request):
    if not request.session.get('cuenta_id') or request.session.get('rol') != ROL_JEFE:
        return redirect('identificacion')

    jefe = get_object_or_404(Cuenta, pk=request.session.get('cuenta_id'))

    # Buscar todas las calificaciones rechazadas por este jefe (sin importar equipo actual)
    rechazadas_ids = CalificacionRechazada.objects.filter(jefe=jefe).values_list('calificacion_id', flat=True)
    base_qs = CalificacionTributaria.objects.filter(
        pk__in=rechazadas_ids,
        estado_calificacion='rechazado'
    )

    # Calificadores únicos de esas calificaciones
    calificadores_ids = base_qs.values_list('cuenta_id', flat=True).distinct()
    calificadores_equipo = list(Cuenta.objects.filter(pk__in=calificadores_ids).order_by('nombre', 'apellido'))

    calificador_id = request.GET.get('calificador_id')
    try:
        page_size = int(request.GET.get('page_size', 10))
    except ValueError:
        page_size = 10
    if page_size not in [10,20,30,40,50]:
        page_size = 10

    if calificador_id:
        try:
            base_qs = base_qs.filter(cuenta_id_id=int(calificador_id))
        except ValueError:
            pass

    calificaciones_qs = base_qs.select_related('cuenta_id', 'rut_empresa').order_by('-fecha_calculo')

    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(calificaciones_qs, page_size)
    page = request.GET.get('page')
    try:
        calificaciones = paginator.page(page)
    except PageNotAnInteger:
        calificaciones = paginator.page(1)
    except EmptyPage:
        calificaciones = paginator.page(paginator.num_pages)

    context = {
        'calificaciones': calificaciones,
        'total_calificaciones': paginator.count,
        'calificadores_equipo': calificadores_equipo,
        'calificador_seleccionado': calificador_id,
        'page_size': page_size,
        'page_obj': calificaciones,
        'paginator': paginator,
    }
    return render(request, 'Contenedor_Calificaciones/jefe_tributario/calificaciones_rechazadas.html', context)


# Acción: aprobar calificación (solo Jefe)
def aprobar_calificacion(request, calificacion_id: int):
    if request.method != 'POST':
        return redirect('calificaciones_pendientes_jefe')
    if not request.session.get('cuenta_id') or request.session.get('rol') != ROL_JEFE:
        return redirect('identificacion')

    jefe = get_object_or_404(Cuenta, pk=request.session.get('cuenta_id'))
    calificacion = get_object_or_404(CalificacionTributaria, pk=calificacion_id)

    # Validar pertenencia al equipo y estado por_aprobar
    if jefe.equipo_trabajo is None or not Cuenta.objects.filter(
        equipo_trabajo=jefe.equipo_trabajo, rol=ROL_CALIFICADOR, cuenta_id=calificacion.cuenta_id_id
    ).exists():
        messages.error(request, 'No puedes aprobar calificaciones fuera de tu equipo.')
        return redirect('calificaciones_pendientes_jefe')
    if calificacion.estado_calificacion != 'por_aprobar':
        messages.error(request, 'La calificación ya no está en estado por aprobar.')
        return redirect('calificaciones_pendientes_jefe')

    observaciones = request.POST.get('observaciones', '').strip()

    try:
        CalificacionAprovada.objects.create(
            calificacion=calificacion,
            jefe=jefe,
            observaciones=observaciones,
        )
        calificacion.estado_calificacion = 'aprobado'
        calificacion.save()
        messages.success(request, f'Se aprobó la calificación #{calificacion.calificacion_id}.')
    except IntegrityError:
        messages.error(request, 'Ya existe un registro de aprobación para esta calificación.')
    except ValidationError as e:
        messages.error(request, f'Error de validación: {e}')

    return redirect('calificaciones_pendientes_jefe')


# Acción: rechazar calificación (solo Jefe)
def rechazar_calificacion(request, calificacion_id: int):
    if request.method != 'POST':
        return redirect('calificaciones_pendientes_jefe')
    if not request.session.get('cuenta_id') or request.session.get('rol') != ROL_JEFE:
        return redirect('identificacion')

    jefe = get_object_or_404(Cuenta, pk=request.session.get('cuenta_id'))
    calificacion = get_object_or_404(CalificacionTributaria, pk=calificacion_id)

    # Validar pertenencia al equipo y estado por_aprobar
    if jefe.equipo_trabajo is None or not Cuenta.objects.filter(
        equipo_trabajo=jefe.equipo_trabajo, rol=ROL_CALIFICADOR, cuenta_id=calificacion.cuenta_id_id
    ).exists():
        messages.error(request, 'No puedes rechazar calificaciones fuera de tu equipo.')
        return redirect('calificaciones_pendientes_jefe')
    if calificacion.estado_calificacion != 'por_aprobar':
        messages.error(request, 'La calificación ya no está en estado por aprobar.')
        return redirect('calificaciones_pendientes_jefe')

    observaciones = request.POST.get('observaciones', '').strip()

    try:
        CalificacionRechazada.objects.create(
            calificacion=calificacion,
            jefe=jefe,
            observaciones=observaciones,
        )
        calificacion.estado_calificacion = 'rechazado'
        calificacion.save()
        messages.success(request, f'Se rechazó la calificación #{calificacion.calificacion_id}.')
    except IntegrityError:
        messages.error(request, 'Ya existe un registro de rechazo para esta calificación.')
    except ValidationError as e:
        messages.error(request, f'Error de validación: {e}')

    return redirect('calificaciones_pendientes_jefe')


# Detalle de una calificación para Jefe (previo a aprobar/rechazar)
def detalle_calificacion_jefe(request, calificacion_id: int):
    if not request.session.get('cuenta_id') or request.session.get('rol') != ROL_JEFE:
        return redirect('identificacion')

    jefe = get_object_or_404(Cuenta, pk=request.session.get('cuenta_id'))
    calificacion = get_object_or_404(
        CalificacionTributaria.objects.select_related('cuenta_id', 'rut_empresa'),
        pk=calificacion_id
    )

    # Validar que la calificación pertenezca a un calificador del equipo del jefe
    pertenece = Cuenta.objects.filter(
        equipo_trabajo=jefe.equipo_trabajo,
        rol=ROL_CALIFICADOR,
        cuenta_id=calificacion.cuenta_id_id
    ).exists()
    if not pertenece:
        messages.error(request, 'No puedes ver calificaciones fuera de tu equipo.')
        return redirect('calificaciones_pendientes_jefe')

    # Opcional: advertir si no está por aprobar
    if calificacion.estado_calificacion != 'por_aprobar':
        messages.info(request, 'Esta calificación ya no está en estado por aprobar.')

    return_url = request.META.get('HTTP_REFERER') or reverse('calificaciones_pendientes_jefe')
    context = {
        'c': calificacion,
        'return_url': return_url,
    }
    return render(request, 'Contenedor_Calificaciones/jefe_tributario/calificacion_detalle_jefe.html', context)


# Vista: mostrar equipo del jefe
def tu_equipo(request):
    """Muestra los calificadores que pertenecen al equipo del jefe autenticado.

    Requiere que la sesión tenga cuenta_id y rol de Jefe. Si el jefe no tiene equipo
    asignado se muestra un mensaje informativo. Para cada calificador se intenta
    recuperar su Cuenta (si existe) para mostrar nombre, apellido y correo; si no
    existe se dejan esos campos en blanco y se marca con X roja en la columna Cuenta.
    """
    if not request.session.get('cuenta_id') or request.session.get('rol') != ROL_JEFE:
        return redirect('identificacion')

    jefe_cuenta = get_object_or_404(Cuenta, pk=request.session.get('cuenta_id'))
    equipo = jefe_cuenta.equipo_trabajo

    calificadores_data = []
    if equipo is not None:
        # Relación intermedia EquipoCalificador -> calificador
        relaciones = EquipoCalificador.objects.filter(equipo=equipo).select_related('calificador')
        for rel in relaciones:
            rut_calificador = rel.calificador.rut
            cuenta_calificador = Cuenta.objects.filter(rut=rut_calificador).first()
            if cuenta_calificador:
                nombre_completo = f"{cuenta_calificador.nombre} {cuenta_calificador.apellido}".strip()
                correo = cuenta_calificador.correo
                tiene_cuenta = True
            else:
                nombre_completo = ''
                correo = ''
                tiene_cuenta = False
            calificadores_data.append({
                'rut': rut_calificador,
                'nombre_completo': nombre_completo,
                'correo': correo,
                'tiene_cuenta': tiene_cuenta,
            })

    context = {
        'equipo': equipo,
        'calificadores': calificadores_data,
    }
    return render(request, 'Contenedor_Calificaciones/jefe_tributario/tu_equipo.html', context)

#Guardar calificaciones masivas
def guardar_calificaciones_masivas(request):
    """
    Vista para guardar las calificaciones válidas de la carga masiva en la BD.
    """
    if not request.session.get('cuenta_id') or not request.session.get('rol') == ROL_CALIFICADOR:
        return redirect('identificacion')
    
    if request. method == 'POST':
        try:
            # Obtener datos del formulario
            datos_json = request.POST.get('datos_json', '')
            accion = request. POST.get('accion', 'por_enviar')
            
            if not datos_json:
                messages.error(request, 'No hay datos válidos para guardar.')
                return redirect('carga_masiva')
            
            # Deserializar datos
            datos_validos = json.loads(datos_json)
            
            if not datos_validos:
                messages. warning(request, 'No hay calificaciones válidas para guardar.')
                return redirect('carga_masiva')
            
            # Obtener cuenta del usuario
            cuenta_id = request.session.get('cuenta_id')
            cuenta = Cuenta.objects.get(pk=cuenta_id)
            
            # Determinar estado según la acción
            if accion == 'por_enviar':
                estado = 'por_enviar'
                mensaje_exito = 'guardadas como Por Enviar'
            elif accion == 'enviar':
                estado = 'por_aprobar'
                mensaje_exito = 'enviadas para aprobación'
            else:
                estado = 'por_enviar'
                mensaje_exito = 'guardadas'
            
            # Guardar calificaciones usando SQL directo
            from django.db import connection
            guardadas = 0
            
            with transaction.atomic():
                with connection.cursor() as cursor:
                    for dato in datos_validos:
                        # Validar que la empresa existe
                        empresa = Empresa.objects.filter(empresa_rut=dato['rut_empresa']).first()
                        if not empresa:
                            continue
                        
                        # Insertar directamente con SQL
                        cursor.execute("""
                            INSERT INTO calificacion_tributaria (
                                cuenta_id, empresa_rut, nombre_empresa, anio_tributario,
                                tipo_calificacion, monto_tributario, factor_tributario,
                                unidad_valor, puntaje_calificacion, categoria_calificacion,
                                nivel_riesgo, justificacion_resultado, metodo_calificacion,
                                estado_calificacion, fecha_calculo
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        """, [
                            cuenta. cuenta_id,
                            dato['rut_empresa'],
                            empresa.nombre_empresa,
                            dato['anio_tributario'],
                            dato['tipo_calificacion'],
                            dato['monto_tributario'],
                            dato['factor_tributario'],
                            dato['unidad_valor'],
                            dato['puntaje_calificacion'],
                            dato['categoria_calificacion'],
                            dato['nivel_riesgo'],
                            dato. get('justificacion_resultado', ''),
                            'masiva',
                            estado
                        ])
                        guardadas += 1
            
            if guardadas > 0:
                messages.success(
                    request, 
                    f'✅ {guardadas} calificación(es) {mensaje_exito} exitosamente.'
                )
            else:
                messages.warning(request, 'No se guardó ninguna calificación.')
            
            return redirect('Inicio_Calificador')
            
        except json.JSONDecodeError:
            messages.error(request, 'Error al procesar los datos.  Intente nuevamente.')
            return redirect('carga_masiva')
        except Cuenta.DoesNotExist:
            messages.error(request, 'Sesión inválida.')
            return redirect('identificacion')
        except Exception as e:
            messages.error(request, f'Error al guardar: {str(e)}')
            return redirect('carga_masiva')
    
    return redirect('carga_masiva')