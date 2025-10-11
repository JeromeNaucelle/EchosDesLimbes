from django import forms
from larp.utils import has_orga_permission
from django.utils.safestring import mark_safe
from larp import models as larp_models
from bootstrap_datepicker_plus.widgets import DatePickerInput


class ProfileForm(forms.ModelForm):
    triggers = forms.ModelMultipleChoiceField(queryset=larp_models.Trigger.objects.all(), 
                                              required=False, 
                                              label=mark_safe("""Avez-vous des désirs de non jeu ? Il est cependant adaptable aux
personnes sensibles. Prenez le temps de vous interroger vraiment sur les
mises en situations mentionnées dans la liste ci-dessous.<br/>
Que vous refusiez de jouer certains aspects est également générateur de
jeu. Le but c'est le respect de votre être et de vos limites. Afin que vous
puissiez passer un bon GN.<br/>
Cochez chacune des cases si vous ne souhaitez pas avoir ce type de jeu
dans votre background et dans vos quêtes"""),
                                              widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = larp_models.Profile
        exclude = ["user", "activated"]
        labels = {
            "food": "Avez vous un régime alimentaire particulier, ou des allergies ?",

            "xp_gn": "Quelle est votre expérience Gnistique ?",

            "unwanted_people": mark_safe("""Y a-t-il des personnes avec qui tu n'es pas à l'aise pour jouer en GN ?
Si oui, merci de mettre à côté de leur nom, un chiffre représentant l'échelle
suivante : <br/>
1 - Je ne souhaite pas de liens forts entre nos personnages, mais je peux interagir
avec cette personne s'il n'y a pas de jeu proche ou intense.<br/>
2 - Je ne souhaite pas avoir de lien avec cette personne en jeu, même sans
implications particulière. Si nos rôles permettent d'éviter des interactions en
jeu, cela ne me dérange pas que cette personne soit présente.<br/>
3 - Je ne pourrai pas venir sur le GN si cette personne est présente.
"""),

            "fears": mark_safe("""Avez-vous des phobies particulières ?
Si oui, merci de mettre à côté de la phobie, un chiffre représentant l'échelle
suivante :<br/>
1 - Je me tiens éloigné et tout va bien.<br/>
2 - Je pars et ne veut plus avoir la source dans mon champ de vision où je
m’échappe de toute situation pouvant faire remonter cette phobie.<br/>
3 - C’est insupportable pour moi et je peux faire un malaise."""),

            "emergency_contact": """Personnes à prévenir en cas d’urgence (Nom, prénom, numéro de
téléphone). Merci de mettre 2 personnes différentes pour être sûr de
pouvoir contacter au moins l’un d’entre eux."""
        }

        widgets = {
            'birthdate': DatePickerInput(options={"format": "DD/MM/YYYY"})
        }


class PnjInfosForm(forms.ModelForm):
    class Meta:
        model = larp_models.PnjInfos
        exclude = ['user', 'larp']
        widgets = {
            "prefered_time": forms.RadioSelect(choices=larp_models.PnjInfos.TIME_PREFERENCE.choices()),
            "nigth_action": forms.RadioSelect(choices=[(True, 'Oui'), (False, 'Non')])
        }
        labels = {
            "prefered_time": "Souhaitez-vous des rôles plutôt matinaux, ou du soir ?",
            "logistic_or_role": "En tant que PNJ, que préférez-vous faire entre la logistique (5) et les rôles proposés dans le jeu (0) ?",
            "importance": "Parmis les rôles qui seront proposés, quel niveau d'importance aimeriez-vous jouer sur le GN ? (0 : Aucune importance, 5 : Important)",
            "talent": "Avez-vous des talents particuliers que vous souhaitez lettre en avant ? (cracheur de feu, jongleur, échassier, chanteur, danseur, etc...)",
            "nigth_action": "Seriez-vous motivé pour faire des rôles de nuit ? (Des rôles en plus, entre 23h et 2h du matin)"
        }

    def __init__(self, *args, **kwargs):
        larp = kwargs['instance'].larp
        user = kwargs.pop('user')
        orga = has_orga_permission(user, larp, False)
        super(PnjInfosForm, self).__init__(*args, **kwargs)
        if not orga:
            self.fields['info_orga'].disabled = True


class PjInfosForm(forms.ModelForm):
    class Meta:
        model = larp_models.PjInfos
        exclude = ['user', 'larp', 'bg_choices']
        labels = {
            'objectives': 'Objectifs de jeu (réservé aux orgas)'
        }

    def __init__(self, *args, **kwargs):
        if 'inscription' in kwargs:
            inscription = kwargs.pop('inscription')
            larp = inscription.opus.larp
        else:
            larp = kwargs.pop('larp')
        user = kwargs.pop('user')

        orga = has_orga_permission(user, larp, False)
        already_existing = True if 'instance' in kwargs else False
        super(PjInfosForm, self).__init__(*args, **kwargs)
        if not orga:
            self.fields['objectives'].disabled = True
        self.fields['faction'].label = larp.factions_name
        self.fields['faction'].disabled = True

        if not already_existing:
            self.fields['faction'].initial = inscription.faction_id


class BgAnswerForm(forms.Form):
    choice = forms.ChoiceField(widget=forms.RadioSelect, label="")
    player_text = forms.CharField(widget=forms.Textarea, required=False, label="Vous pouvez ajouter des éléments (restera possible plus tard)")

    def __init__(self, *args, **kwargs):
        choices_qs = kwargs.pop('choices_qs')
        super().__init__(*args, **kwargs)
        # Display the choice text for the radio options
        self.fields['choice'].choices = [(str(c.pk), c.text or c.short_name) for c in choices_qs]
