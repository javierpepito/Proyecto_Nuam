from django.urls import path
from . import views

urlpatterns = [
    path("", views.identificacion_view, name="identificacion"),  # Home: ingreso de RUT
    path("login/", views.login_view, name="login"),
    path("inicio_calificador/", views.Inicio_Calificador, name="Inicio_Calificador"),
    path("registrar_empresa/", views.registrar_empresa, name="registrar_empresa"),
    path("empresas/", views.lista_empresas, name="lista_empresas"),
    path("logout/", views.logout_view, name="logout"),
    path("añadir_calificacion/", views.agregar_calificacion_manual, name="Añadir_calificacion_manual"),
    path("inicio_jefe/", views.Inicio_Jefe, name="Inicio_Jefe"),
    path("agregar_calificacion_manual/", views.agregar_calificacion, name="agregar_calificacion"),
    path("carga_masiva/", views.carga_masiva_view, name="carga_masiva"),
]