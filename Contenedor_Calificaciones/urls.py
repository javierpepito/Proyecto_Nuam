from django.urls import path, include
from . import views
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Router para DRF
router = routers.DefaultRouter()
router.register(r"cuentas", views.CuentaViewSet, basename='cuenta')
router.register(r"equipos", views.EquipoDeTrabajoViewSet, basename='equipo')
router.register(r"empresas", views.EmpresaViewSet, basename='empresa')
router.register(r"calificaciones", views.CalificacionTributariaViewSet, basename='calificacion')
router.register(r"calificaciones-aprobadas", views.CalificacionAprovadaViewSet, basename='calificacion-aprobada')
router.register(r"calificaciones-rechazadas", views.CalificacionRechazadaViewSet, basename='calificacion-rechazada')

urlpatterns = [
    path("", views.identificacion_view, name="identificacion"),  # Home: ingreso de RUT
    
    # API REST
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api/login/", views.LoginAPIView.as_view(), name="api-login"),
    path("api/estadisticas/", views.EstadisticasAPIView.as_view(), name="api-estadisticas"),
    
    # JWT Tokens
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