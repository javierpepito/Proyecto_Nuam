from django.urls import path
from . import views

urlpatterns = [
    path("", views.Inicio_Calificador, name="Inicio_Calificador"),
    #path("calificador/inicio/", views.Inicio_Calificador, name="Inicio_Calificador"),
]