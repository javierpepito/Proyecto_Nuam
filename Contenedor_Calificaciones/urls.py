from django.urls import path, include
from . import views
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Router para DRF (opcional, no se usa en la app móvil simplificada)
router = routers.DefaultRouter()

urlpatterns = [
    path("", views.identificacion_view, name="identificacion"),  # Home: ingreso de RUT
    
    # ========================================
    # API REST PARA APP MÓVIL DEL JEFE
    # ========================================
    
    # Autenticación
    path("api/login/", views.LoginAPIView.as_view(), name="api-login"),
    
    # Dashboard principal
    path("api/dashboard/", views.DashboardAPIView.as_view(), name="api-dashboard"),
    path("api/debug-aprobadas/", views.DebugAprobadasAPIView.as_view(), name="api-debug-aprobadas"),
    
    # Calificaciones pendientes (por aprobar)
    path("api/calificaciones-pendientes/", views.CalificacionesPendientesAPIView.as_view(), name="api-calificaciones-pendientes"),
    path("api/calificacion/<int:calificacion_id>/", views.CalificacionDetalleAPIView.as_view(), name="api-calificacion-detalle"),
    
    # Acciones: Aprobar/Rechazar
    path("api/aprobar-calificacion/", views.AprobarCalificacionAPIView.as_view(), name="api-aprobar-calificacion"),
    path("api/rechazar-calificacion/", views.RechazarCalificacionAPIView.as_view(), name="api-rechazar-calificacion"),
    
    # Historial (aprobadas y rechazadas)
    path("api/historial/", views.HistorialCalificacionesAPIView.as_view(), name="api-historial"),
    
    # Equipo del jefe
    path("api/mi-equipo/", views.MiEquipoAPIView.as_view(), name="api-mi-equipo"),
    
    # Perfil del jefe
    path("api/perfil/", views.PerfilJefeAPIView.as_view(), name="api-perfil"),
    
    # JWT Tokens (opcional para autenticación avanzada)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Vistas web
    path("login/", views.login_view, name="login"),
    path("registro/", views.registro_view, name="registro"),
    path("inicio_calificador/", views.Inicio_Calificador, name="Inicio_Calificador"),
    path("registrar_empresa/", views.registrar_empresa, name="registrar_empresa"),
    path("empresas/", views.lista_empresas, name="lista_empresas"),
    path("logout/", views.logout_view, name="logout"),
    path("inicio_jefe/", views.Inicio_Jefe, name="Inicio_Jefe"),
    path("agregar_calificacion/", views.agregar_calificacion, name="agregar_calificacion"),
    path("carga_masiva/", views.carga_masiva_view, name="carga_masiva"),
    path("guardar_calificaciones_masivas/", views.guardar_calificaciones_masivas, name="guardar_calificaciones_masivas"),
    path("tus_calificaciones/", views.tus_calificaciones, name="tus_calificaciones"),
    path("calificaciones_pendientes/", views.calificaciones_pendientes, name="calificaciones_pendientes"),
    path("calificaciones/editar/<int:calificacion_id>/", views.editar_calificacion_pendiente, name="editar_calificacion_pendiente"),
    path("calificaciones/eliminar/<int:calificacion_id>/", views.eliminar_calificacion_pendiente, name="eliminar_calificacion_pendiente"),
    path("calificaciones/enviar/<int:calificacion_id>/", views.enviar_calificacion_pendiente, name="enviar_calificacion_pendiente"),
    # Rutas Jefe: calificaciones pendientes del equipo y acciones
    path("jefe/calificaciones_pendientes/", views.calificaciones_pendientes_jefe, name="calificaciones_pendientes_jefe"),
    path("jefe/calificaciones_aprobadas/", views.calificaciones_aprobadas_jefe, name="calificaciones_aprobadas_jefe"),
    path("jefe/calificaciones_rechazadas/", views.calificaciones_rechazadas_jefe, name="calificaciones_rechazadas_jefe"),
    path("jefe/tu_equipo/", views.tu_equipo, name="tu_equipo"),
    path("jefe/calificaciones/<int:calificacion_id>/", views.detalle_calificacion_jefe, name="detalle_calificacion_jefe"),
    path("jefe/calificaciones/aprobar/<int:calificacion_id>/", views.aprobar_calificacion, name="aprobar_calificacion"),
    path("jefe/calificaciones/rechazar/<int:calificacion_id>/", views.rechazar_calificacion, name="rechazar_calificacion"),
    path("jefe/perfil/", views.perfil_jefe, name="perfil_jefe"),
    path("calificador/perfil/", views.perfil_calificador, name="perfil_calificador"),
]