from django.db.models.signals import pre_save, post_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from larp import models as larp_models
from django.contrib.auth.models import Group, User


@receiver(pre_save)
def on_pre_save(sender, instance, **kwargs):
    # On crée un groupe d'orga pour chaque GN créée
    if sender == larp_models.Larp and not instance.pk:
        orga_group = Group.objects.create(name=f"Orgas - {instance.name}")
        instance.orga_group = orga_group

    # Si l'inscription est pour un PNJ, on lui crée une fiche PNJ pour ce GN
    if sender == larp_models.Inscription and not instance.pk:
        access_type = instance.access_type
        if access_type == larp_models.AccessType.PNJF or \
            access_type == larp_models.AccessType.PNJV:
            defaults = {
                'user': instance.user,
                'larp': instance.opus.larp
            }
            larp_models.PnjInfos.objects.get_or_create(
                defaults=defaults,
                user=instance.user,
                larp=instance.opus.larp)
            

@receiver(post_save)
def on_pre_save(sender, instance, created, **kwargs):
    if sender == User and created:
        profile = larp_models.Profile.objects.create(user=instance)
        profile.save()
    

        
@receiver(user_logged_in)
def check_if_orga(sender, user : User, request, **kwargs):
    if user.is_superuser:
        request.session['is_orga'] = True
        return
    user_groups_id = user.groups.all().values_list('pk')
    user_orga_larps = larp_models.Larp.objects.filter(orga_group_id__in=user_groups_id)
    is_orga = True if user_orga_larps.count() > 0 else False
    request.session['is_orga'] = is_orga

