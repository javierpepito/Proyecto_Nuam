from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Empresa, Cuenta, CalificacionTributaria
from .forms import CalificacionTributariaForm
from .validators import validate_rut_chileno, formatear_rut

import pandas as pd
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

#Variables constantes para los roles:
ROL_JEFE = 'Jefe De Equipo'
ROL_CALIFICADOR = 'Calificador Tributario'

#Vista inicial del calificador tributario
def Inicio_Calificador(request):
    if not request.session.get('cuenta_id') or not request.session.get('rol') == ROL_CALIFICADOR: 
        #Al redirigir a indetificarse no se le da a entender que es una vista unica para jefes, podrian ser dos if que redirigian a dos pantallas distintas y una de esas la pantalla de advertencia.
        return redirect('identificacion')
    return render(request, 'Contenedor_Calificaciones/calificador_tributario/inicio_calificador.html')

#Vista inicial del jefe
def Inicio_Jefe(request):
    if not request.session.get('cuenta_id') or not request.session.get('rol') == ROL_JEFE:
        return redirect('identificacion')
    return render(request, 'Contenedor_Calificaciones/jefe_tributario/inicio_jefe.html')

def identificacion_view(request):
    """Primera etapa: solicita solo el RUT y redirige a login para ingresar contraseña.
    Si el RUT no existe, se marca bandera para mostrar mensaje en login."""
    mensaje = None
    if request.method == 'POST':
        rut_input = request.POST.get('rut', '').strip()
        if rut_input:
            # Validar/formatear si posible
            try:
                validate_rut_chileno(rut_input)
                rut_formateado = formatear_rut(rut_input)
            except ValidationError:
                # Mantener tal cual si inválido; login mostrará mensaje de no afiliado
                rut_formateado = rut_input
            request.session['rut_identificado'] = rut_formateado
            cuenta = Cuenta.objects.filter(rut=rut_formateado).first()
            if cuenta:
                request.session['nombre_identificado'] = cuenta.nombre
                request.session['apellido_identificado'] = cuenta.apellido
                request.session['cuenta_rol'] = cuenta.rol
                request.session.pop('rut_invalido', None)
            else:
                request.session['nombre_identificado'] = None
                request.session['apellido_identificado'] = None
                request.session['rut_invalido'] = True
            # Reiniciar intentos y bloqueo al iniciar nueva identificación
            request.session['login_attempts'] = 0
            request.session.pop('login_block_until', None)
            return redirect('login')
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
            # Obtener el RUT validado y formateado del formulario
            rut_empresa = form.cleaned_data['rut_empresa']
            
            # Buscar la empresa (ya validamos que existe en clean_rut_empresa)
            try:
                empresa = Empresa.objects.get(empresa_rut=rut_empresa)
            except Empresa.DoesNotExist:
                # Este caso no debería ocurrir por la validación, pero por seguridad:
                messages.error(request, f'La empresa con RUT {rut_empresa} no existe. Por favor regístrela primero.')
                context = {'form': form}
                return render(request, 'Contenedor_Calificaciones/calificador_tributario/calificacion_manual.html', context)
            
            # Crear el objeto sin guardar aún
            calificacion = form.save(commit=False)
            
            # CRÍTICO: Asignar la FK ANTES de cualquier validación o guardado
            calificacion.rut_empresa = empresa
            calificacion.nombre_empresa = empresa.nombre_empresa 
            calificacion.cuenta_id = cuenta
            calificacion.metodo_calificacion = 'manual'
            
            # Determinar el estado según el botón presionado
            if accion == 'pendiente':
                calificacion.estado_calificacion = 'pendiente'
                mensaje = 'Calificación guardada como Pendiente exitosamente.'
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
                return redirect('Inicio_Calificador')
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
            errores_globales.append('El archivo debe ser formato Excel (.xlsx o .xls)')
        else:
            try:
                # Leer el archivo Excel
                df = pd.read_excel(archivo, engine='openpyxl')
                
                # Validar que no esté vacío
                if df.empty:
                    errores_globales.append('El archivo Excel está vacío.')
                else:
                    # Mapeo de columnas esperadas (según tu imagen del Excel)
                    columnas_esperadas = {
                        'Nº': 'numero',
                        'RUT de la Empresa': 'rut_empresa',
                        'Nombre de la Empresa': 'nombre_empresa',
                        'Año Tributario': 'anio_tributario',
                        'Tipo de Calificacion': 'tipo_calificacion',
                        'Monto Tributario': 'monto_tributario',
                        'Factor Tributario': 'factor_tributario',
                        'Unidad de Valor': 'unidad_valor',
                        'Puntaje de Calificación': 'puntaje_calificacion',
                        'Categoría de la Calificación': 'categoria_calificacion',
                        'Nivel de Riesgo': 'nivel_riesgo',
                        'Justificación del resultado (Observaciones)': 'justificacion_resultado'
                    }
                    
                    # Renombrar columnas para trabajar más fácil
                    df.columns = df.columns.str.strip()
                    
                    # Validar que existan las columnas necesarias
                    columnas_faltantes = []
                    for col_excel in columnas_esperadas.keys():
                        if col_excel not in df.columns:
                            columnas_faltantes.append(col_excel)
                    
                    if columnas_faltantes:
                        errores_globales.append(f"Faltan columnas en el Excel: {', '.join(columnas_faltantes)}")
                    else:
                        # Procesar cada fila (máximo 10)
                        filas_procesadas = 0
                        
                        for index, row in df.iterrows():
                            # Saltar filas vacías
                            if pd.isna(row['RUT de la Empresa']) or str(row['RUT de la Empresa']).strip() == '':
                                continue
                            
                            if filas_procesadas >= 10:
                                errores_globales.append('⚠️ Se permiten máximo 10 calificaciones por archivo. Las filas adicionales fueron ignoradas.')
                                break
                            
                            filas_procesadas += 1
                            errores_fila = []
                            
                            # Validar RUT empresa (debe existir en BD)
                            rut_empresa_valor = str(row['RUT de la Empresa']).strip()
                            try:
                                validate_rut_chileno(rut_empresa_valor)
                                rut_formateado = formatear_rut(rut_empresa_valor)
                                empresa = Empresa.objects.filter(empresa_rut=rut_formateado).first()
                                
                                if not empresa:
                                    errores_fila.append(f'Empresa con RUT {rut_formateado} no está registrada.')
                            except ValidationError as e:
                                errores_fila.append(f'RUT inválido: {rut_empresa_valor}')
                                rut_formateado = rut_empresa_valor
                                empresa = None
                            
                            # Validar año tributario
                            try:
                                anio = int(row['Año Tributario'])
                                if anio < 1900 or anio > timezone.now().year:
                                    errores_fila.append(f'Año tributario {anio} fuera de rango (1900-{timezone.now().year})')
                            except (ValueError, TypeError):
                                errores_fila.append(f'Año tributario inválido: {row["Año Tributario"]}')
                                anio = None
                            
                            # Validar monto tributario
                            try:
                                monto = float(row['Monto Tributario'])
                                if monto < 0:
                                    errores_fila.append('Monto tributario no puede ser negativo')
                            except (ValueError, TypeError):
                                errores_fila.append(f'Monto tributario inválido: {row["Monto Tributario"]}')
                                monto = None
                            
                            # Validar factor tributario
                            try:
                                factor = float(row['Factor Tributario'])
                                if factor < 0:
                                    errores_fila.append('Factor tributario no puede ser negativo')
                            except (ValueError, TypeError):
                                errores_fila.append(f'Factor tributario inválido: {row["Factor Tributario"]}')
                                factor = None
                            
                            # Validar puntaje (0-100)
                            try:
                                puntaje = int(row['Puntaje de Calificación'])
                                if puntaje < 0 or puntaje > 100:
                                    errores_fila.append('Puntaje debe estar entre 0 y 100')
                            except (ValueError, TypeError):
                                errores_fila.append(f'Puntaje inválido: {row["Puntaje de Calificación"]}')
                                puntaje = None
                            
                            # Validar categoría
                            categoria_map = {
                                'bajo': 'bajo',
                                'medio': 'medio',
                                'alto': 'alto',
                                'BAJO': 'bajo',
                                'MEDIO': 'medio',
                                'ALTO': 'alto',
                                'Bajo': 'bajo',
                                'Medio': 'medio',
                                'Alto': 'alto'
                            }
                            categoria_valor = str(row['Categoría de la Calificación']).strip()
                            if categoria_valor not in categoria_map:
                                errores_fila.append(f'Categoría inválida: {categoria_valor}. Debe ser: Bajo, Medio o Alto')
                                categoria = None
                            else:
                                categoria = categoria_map[categoria_valor]
                            
                            # Validar nivel de riesgo
                            riesgo_map = {
                                'bajo': 'bajo',
                                'medio': 'medio',
                                'alto': 'alto',
                                'critico': 'critico',
                                'crítico': 'critico',
                                'BAJO': 'bajo',
                                'MEDIO': 'medio',
                                'ALTO': 'alto',
                                'CRITICO': 'critico',
                                'CRÍTICO': 'critico',
                                'Bajo': 'bajo',
                                'Medio': 'medio',
                                'Alto': 'alto',
                                'Critico': 'critico',
                                'Crítico': 'critico'
                            }
                            riesgo_valor = str(row['Nivel de Riesgo']).strip()
                            if riesgo_valor not in riesgo_map:
                                errores_fila.append(f'Nivel de riesgo inválido: {riesgo_valor}. Debe ser: Bajo, Medio, Alto o Crítico')
                                riesgo = None
                            else:
                                riesgo = riesgo_map[riesgo_valor]
                            
                            # Agregar datos procesados
                            datos_procesados.append({
                                'fila': index + 2,  # +2 porque Excel empieza en 1 y tiene header
                                'rut_empresa': rut_formateado if rut_formateado else rut_empresa_valor,
                                'nombre_empresa': str(row['Nombre de la Empresa']).strip() if pd.notna(row['Nombre de la Empresa']) else '',
                                'anio_tributario': anio,
                                'tipo_calificacion': str(row['Tipo de Calificacion']).strip() if pd.notna(row['Tipo de Calificacion']) else '',
                                'monto_tributario': monto,
                                'factor_tributario': factor,
                                'unidad_valor': str(row['Unidad de Valor']).strip() if pd.notna(row['Unidad de Valor']) else '',
                                'puntaje_calificacion': puntaje,
                                'categoria_calificacion': categoria,
                                'nivel_riesgo': riesgo,
                                'justificacion_resultado': str(row['Justificación del resultado (Observaciones)']).strip() if pd.notna(row['Justificación del resultado (Observaciones)']) else '',
                                'errores': errores_fila,
                                'valido': len(errores_fila) == 0
                            })
                        
                        if filas_procesadas == 0:
                            errores_globales.append('No se encontraron filas válidas con datos en el archivo.')
                            
            except Exception as e:
                errores_globales.append(f'Error al procesar el archivo: {str(e)}')
    
    context = {
        'datos_procesados': datos_procesados,
        'errores_globales': errores_globales,
        'archivo_nombre': archivo_nombre,
        'total_registros': len(datos_procesados),
        'registros_validos': sum(1 for d in datos_procesados if d['valido']),
        'registros_con_errores': sum(1 for d in datos_procesados if not d['valido']),
    }
    
    return render(request, 'Contenedor_Calificaciones/calificador_tributario/carga_masiva.html', context)