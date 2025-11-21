from django.apps import AppConfig


class ContenedorCalificacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Contenedor_Calificaciones'

    def ready(self):
        # Importa signals para actualizar cuentas al modificar equipos
        from . import signals  # noqa: F401
