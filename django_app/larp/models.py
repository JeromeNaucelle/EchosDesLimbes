from datetime import date
from django.db import models
from django.contrib.auth.models import User, Group
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Q
from enum import Enum

# Create your models here.
VALIDATION_STEPS = (
    ("unlocked", "Débloqué"),
    ("player_validated", "Validé par joueur"),
    ("orga_locked", "Validé par orga"),
)

NB_STEPS = 10

class AccessType(models.TextChoices):
    PJ      = "PJ", "Joueur"
    PNJV    = "PNJV", "PNJ volant"
    PNJF    = "PNJF", "PNJ de faction"



class Trigger(models.Model):
    nom = models.CharField(
        max_length=50,
        unique=True
    )
    
    def __str__(self):
        return self.nom


class Profile(models.Model):
    class Meta:
        verbose_name = "Profil utilisateur"

    class XP_GN(Enum):
        ONE      = "Je suis un débutant"
        TWO      = "1 à 2 GNs, je découvre encore"
        THREE    = "3 à 5 GNs, je suis un habitué maintenant"
        FOUR     = "5+ GNs, je vis pour le GN désormais"

        @classmethod
        def choices(cls):
            return [(key.name, key.value) for key in cls]


    user        = models.OneToOneField(User, on_delete=models.CASCADE)
    pseudos     = models.TextField(verbose_name="Pseudos sur les réseaux sociaux :")
    birthdate   = models.DateField(verbose_name="Date de naissance :", null=True)
    food        = models.TextField(verbose_name="Régime alimentaire", blank=True, default='')
    xp_gn       = models.CharField(choices=XP_GN.choices(), blank=False, default=XP_GN.ONE, max_length=10)
    unwanted_people = models.TextField(verbose_name="Des gens avec qui vous ne souhaitez pas jouer",blank=True, default='')
    fears       = models.TextField("Phobies", default='', blank=True)
    triggers    = models.ManyToManyField(Trigger, blank=True)
    emergency_contact = models.TextField("Contacts d'urgence", default='')
    activated = models.BooleanField(default=False)

    def __str__(self):
        fullname = f"{self.user.first_name} {self.user.last_name} ({self.user.get_username()})"
        return fullname



def step_validators():
    return [
        MaxValueValidator(limit_value=NB_STEPS, message=f"C'est le numéro de la question, il doit être compris entre 0 et {NB_STEPS}"),
        MinValueValidator(limit_value=0, message=f"C'est le numéro de la question, il doit être compris entre 0 et {NB_STEPS}")
        ]

class Larp(models.Model):
    class Meta:
        verbose_name = "GN"

    name    = models.CharField(max_length=70, unique=True, verbose_name="Nom")
    description  = models.TextField(default="", blank=True)
    factions_name = models.CharField(verbose_name="Dénomination des groupes (Faction, Gang...)", max_length=35)
    orga_group    = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name
    
class Opus(models.Model):
    class Meta:
        verbose_name_plural = "Opus"

    larp    = models.ForeignKey(Larp, on_delete=models.DO_NOTHING)
    name    = models.CharField(max_length=70, unique=True, verbose_name="Nom")
    date    = models.DateField(blank=True, null=True)
    description  = models.TextField(default="", blank=True)
    location     = models.TextField(blank=True, verbose_name="Lieu")
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    

class Faction(models.Model):
    class Meta:
        verbose_name = "Faction"

    larp    = models.ForeignKey(Larp, on_delete=models.DO_NOTHING, verbose_name="GN")
    name    = models.CharField(max_length=70, unique=True, verbose_name="Nom")
    orga    = models.ForeignKey(User, blank=True, null=True, on_delete=models.DO_NOTHING)
    orga_contact = models.TextField(default="", blank=True, verbose_name="Info de contact orga")


    def __str__(self):
        return self.name
    


class PnjInfos(models.Model):
    class Meta:
        verbose_name = "Infos PNJ"

    class TIME_PREFERENCE(Enum):
        EARLY = "Première tâche 6h30"
        LATE  = "Dernière tâche entre 23h et 2h"
        ANY   = "Sans préférence"

        @classmethod
        def choices(cls):
            return [(key.name, key.value) for key in cls]

        
    class SIX_CHOICES(Enum):
        ZERO = 0
        ONE = 1
        TWO = 2
        THREE = 3
        FOUR = 4
        FIVE = 5

        @classmethod
        def choices(cls):
            return [(key.name, key.value) for key in cls]
    

    user        = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    larp        = models.ForeignKey(Larp, on_delete=models.CASCADE)
    info_orga       = models.TextField(blank=True, default="")
    prefered_time   = models.CharField(choices=TIME_PREFERENCE.choices(), 
                                       blank=False,
                                       default='',
                                       max_length=10,
                                       null=True)
    nigth_action    = models.BooleanField(verbose_name="Action de nuit", null=True)
    logistic_or_role= models.CharField(choices=SIX_CHOICES.choices(), null=True, max_length=6)
    importance      = models.CharField(choices=SIX_CHOICES.choices(), null=True, max_length=6)
    talent          = models.TextField(blank=True, default="", null=True)
    

class Inscription(models.Model):
    class Meta:
        verbose_name = "Inscription"
        constraints = [
            models.UniqueConstraint(fields=["user", "opus"], name="unique_inscription")
        ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    opus = models.ForeignKey(Opus, on_delete=models.CASCADE, verbose_name="Opus")
    access_type = models.CharField(verbose_name="Type (PJ, PNJ...)", choices=AccessType, max_length=15, default="PJ")
    faction     = models.ForeignKey(Faction, on_delete=models.DO_NOTHING, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.opus}"
    

class Ticket(models.Model):
    class Meta:
        verbose_name = "Billet"

    opus = models.ForeignKey(Opus, on_delete=models.CASCADE, verbose_name="Opus")
    price = models.FloatField(verbose_name="Prix", default=1.0)
    access_type = models.CharField(verbose_name="Type (PJ, PNJ...)", choices=AccessType, max_length=15)


    def __str__(self):
        return f"{self.access_type} - {self.opus}"
    

class BgStep(models.Model):
    class Meta:
        verbose_name = "Question background"
        verbose_name_plural = "Questions de background"
        constraints = [
            models.UniqueConstraint(fields=["step", "faction"], name="unique_bg_step_per_faction"),
        ]

    step = models.IntegerField(default=0, validators=step_validators())
    faction    = models.ForeignKey(Faction, on_delete=models.CASCADE)
    short_name = models.CharField(verbose_name="Nom (court)", max_length=20)
    question = models.TextField()
    

class BgChoice(models.Model):
    class Meta:
        verbose_name = "Choix de background"
        verbose_name_plural = "Choix de background"
        constraints = [
            models.UniqueConstraint(fields=["short_name", "bg_step"], name="unique_choice_per_step")
        ]

    bg_step = models.ForeignKey(BgStep, on_delete=models.CASCADE, verbose_name="Question background")
    short_name = models.CharField(verbose_name="Nom (court)", max_length=20)
    text = models.TextField(default="", null=True)
    empty = models.BooleanField(default=False, verbose_name="A remplir par le joueur")


class Character_Bg_choices(models.Model):
    class Meta:
        verbose_name = "Choix background des perso"
        verbose_name_plural = "Choix background des perso"
        constraints = [
            models.UniqueConstraint(fields=["pjInfos", "step"], name="unique_bg_choice_per_charac")
        ]

    pjInfos = models.ForeignKey("PjInfos", on_delete=models.CASCADE, null=True)
    bgchoice = models.ForeignKey("BgChoice", on_delete=models.CASCADE)
    player_text = models.TextField(blank=True, default="")
    step = models.IntegerField(default=0, validators=step_validators())


class PjInfos(models.Model):
    class EMOTION_PREFERENCE(Enum):
        SOFT        = "Soft, je veux un jeu doux"
        MOD_POSITIF = "Modéré Positif, je suis ok pour vivre des événements heureux"
        MOD_ALL     = "Modéré toutes émotions"
        SURPRISE    = "Surprenez-moi, vous avez carte blanche"
        INTENSE     = "Intense, je suis motivé.e pour du drama"

        @classmethod
        def choices(cls):
            return [(key.name, key.value) for key in cls]
        
    class Meta:
        verbose_name = "Infos PJ"

    user        = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    larp        = models.ForeignKey(Larp, on_delete=models.CASCADE)
    name        = models.CharField(max_length=60, verbose_name="Nom du personnage")
    faction     = models.ForeignKey(Faction, on_delete=models.DO_NOTHING)
    skills      = models.TextField(verbose_name="Compétences")
    last_learned= models.CharField(max_length=60, verbose_name="Compétence apprise lors du dernier opus", blank=True, default='')
    emotions    = models.CharField(choices=EMOTION_PREFERENCE.choices(), blank=False, default=[EMOTION_PREFERENCE.SOFT], max_length=25)
    objectives  = models.TextField(verbose_name="Objectifs de jeu", blank=True, default='')
    bg_choices = models.ManyToManyField(BgChoice, blank=True, through="Character_Bg_choices")

    def get_parts(self) -> list[str]: 
        result = []
        though_table = self.bg_choices.through
        charac_choices = though_table.objects.filter(pjInfos=self).order_by("step").prefetch_related("bgchoice")
        for charac_choice in charac_choices:
            choice = charac_choice.bgchoice
            text = choice.text
            if text is None or text == "":
                text = "[Texte manquant]"
            #step_name = BgChoiceType[choice.type].value
            step_name = choice.short_name
            result.append((step_name, text))
        return result

    def reset(self):
        though_table = self.bg_choices.through
        though_table.objects.filter(pjInfos=self).delete()
        self.save()



