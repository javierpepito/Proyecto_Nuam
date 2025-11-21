from django.shortcuts import render

# Create your views here.

#Vista para ver html base
def base(request):
    return render(request, 'Contenedor_Calificaciones/base.html')