from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Empresa, Cuenta
from .validators import validate_rut_chileno, formatear_rut
    
# Create your views here.

#Vista inicial de calificador tributario
def Inicio_Calificador(request):
    if not request.session.get('cuenta_id'):
        return redirect('identificacion')
    return render(request, 'Contenedor_Calificaciones/calificador_tributario/inicio_calificador.html')

#Vista temporal para añadir calificacion manualmente
def Añadir_calificacion_manual(request):
    if not request.session.get('cuenta_id'):
        return redirect('identificacion')
    return render(request, 'Contenedor_Calificaciones/calificador_tributario/calificacion_manual.html')


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
                request.session['login_attempts'] = 0
                request.session.pop('login_block_until', None)
                return redirect('Inicio_Calificador')
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
# "Jefe De Equipo" y "Calificador Tributario" coleccion "cuenta"

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
    return render(request, 'Contenedor_Calificaciones/registrar_empresa.html', {"form": form})


def lista_empresas(request):
    if not request.session.get('cuenta_id'):
        return redirect('identificacion')
    empresas = Empresa.objects.select_related('ingresado_por').all().order_by('-fecha_ingreso')
    return render(request, 'Contenedor_Calificaciones/lista_empresas.html', {"empresas": empresas})


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