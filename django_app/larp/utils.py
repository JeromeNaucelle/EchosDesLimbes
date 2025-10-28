from django.http import HttpRequest
from larp import models as larp_models
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied


class CurrentInscription():
    def __init__(self, inscription: larp_models.Inscription):
        self.access_type = inscription.access_type
        self.created_at = inscription.created_at
        self.can_add_character = False
        self.larp_id = inscription.opus.larp.pk
        self.inscription_id = inscription.pk

        if self.access_type == larp_models.AccessType.PJ or self.access_type == larp_models.AccessType.PNJF:
            self.pj_infos = larp_models.PjInfos.objects.filter(user=inscription.user)

            if len(self.pj_infos) < 2:
                self.can_add_character = True

        if self.access_type == larp_models.AccessType.PNJF or self.access_type == larp_models.AccessType.PNJV:
            self.pnj_infos = larp_models.PnjInfos.objects.get(user=inscription.user, larp=inscription.opus.larp)


"""
Retourne un dictionnaire sous la forme
[larp_name] -> inscription
"""
def only_last_inscriptions(user: User):
    
    inscriptions = larp_models.Inscription.objects.select_related('opus__larp').filter(user=user)
    larps = {}
    for i in inscriptions:
        if not i.opus.larp.name in larps:
            larps[i.opus.larp.name] = CurrentInscription(i)
        else:
            current_inscription = larps[i.opus.larp.name]
            if i.created_at > current_inscription.created_at:
                larps[i.opus.larp.name] = CurrentInscription(i)

    return larps


def has_orga_permission(user: User, larp: larp_models.Larp, raise_exception=True):
    if user.is_superuser:
        return True
    if user.groups.filter(pk=larp.orga_group.pk).exists():
        return True
    if raise_exception:
            raise PermissionDenied


def orga_or_denied(request:HttpRequest, raise_exception=True):
    user = request.user
    
    if user.is_superuser:
        return True
    if request.session.get('is_orga', False):
        return True
    if raise_exception:
            raise PermissionDenied
