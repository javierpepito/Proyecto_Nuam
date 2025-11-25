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
]