from django.urls import path
from . import views

urlpatterns = [
    path("", views.identificacion_view, name="identificacion"),  # Home: ingreso de RUT
    path("login/", views.login_view, name="login"),
    path("registro/", views.registro_view, name="registro"),
    path("inicio_calificador/", views.Inicio_Calificador, name="Inicio_Calificador"),
    path("registrar_empresa/", views.registrar_empresa, name="registrar_empresa"),
    path("empresas/", views.lista_empresas, name="lista_empresas"),
    path("logout/", views.logout_view, name="logout"),
    path("inicio_jefe/", views.Inicio_Jefe, name="Inicio_Jefe"),
    path("agregar_calificacion/", views.agregar_calificacion, name="agregar_calificacion"),
    path("carga_masiva/", views.carga_masiva_view, name="carga_masiva"),
    path("tus_calificaciones/", views.tus_calificaciones, name="tus_calificaciones"),
    path("calificaciones_pendientes/", views.calificaciones_pendientes, name="calificaciones_pendientes"),
    # Rutas Jefe: calificaciones pendientes del equipo y acciones
    path("jefe/calificaciones_pendientes/", views.calificaciones_pendientes_jefe, name="calificaciones_pendientes_jefe"),
    path("jefe/calificaciones/<int:calificacion_id>/", views.detalle_calificacion_jefe, name="detalle_calificacion_jefe"),
    path("jefe/calificaciones/aprobar/<int:calificacion_id>/", views.aprobar_calificacion, name="aprobar_calificacion"),
    path("jefe/calificaciones/rechazar/<int:calificacion_id>/", views.rechazar_calificacion, name="rechazar_calificacion"),
]