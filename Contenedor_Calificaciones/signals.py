from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import EquipoCalificador, Cuenta, EquipoDeTrabajo

# Guardar el jefe anterior para actualizar su cuenta si se cambia
@receiver(pre_save, sender=EquipoDeTrabajo)
def equipo_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = EquipoDeTrabajo.objects.get(pk=instance.pk)
            instance._old_jefe_rut = original.jefe_equipo_rut.rut if original.jefe_equipo_rut else None
        except EquipoDeTrabajo.DoesNotExist:
            instance._old_jefe_rut = None
    else:
        instance._old_jefe_rut = None

@receiver(post_save, sender=EquipoDeTrabajo)
def equipo_post_save(sender, instance, created, **kwargs):
    # Si cambió el jefe, limpiar la cuenta anterior
    old_rut = getattr(instance, '_old_jefe_rut', None)
    new_rut = instance.jefe_equipo_rut.rut if instance.jefe_equipo_rut else None
    if old_rut and old_rut != new_rut:
        Cuenta.objects.filter(rut=old_rut).update(equipo_trabajo=None)
    if new_rut:
        Cuenta.objects.filter(rut=new_rut).update(equipo_trabajo=instance)

@receiver(post_save, sender=EquipoCalificador)
def calificador_post_save(sender, instance, created, **kwargs):
    # Asignar equipo a la cuenta del calificador
    Cuenta.objects.filter(rut=instance.calificador.rut).update(equipo_trabajo=instance.equipo)

@receiver(post_delete, sender=EquipoCalificador)
def calificador_post_delete(sender, instance, **kwargs):
    # Quitar equipo de la cuenta del calificador al removerlo
    Cuenta.objects.filter(rut=instance.calificador.rut).update(equipo_trabajo=None)
