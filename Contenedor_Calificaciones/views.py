from django.shortcuts import render

# Create your views here.

#Vista inicial de calificador tributario
def Inicio_Calificador(request):
    return render(request, 'Contenedor_Calificaciones/Inicio_Calificador.html')