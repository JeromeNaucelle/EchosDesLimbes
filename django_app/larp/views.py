from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http.request import HttpRequest
from django.contrib.auth.models import User, Group
from django.db import models

from .models import Profile, Inscription, PnjInfos,PjInfos, Larp, Opus, BgStep, BgChoice, Character_Bg_choices
from .forms import PnjInfosForm, PjInfosForm, BgAnswerForm
from larp.forms import ProfileForm
from larp.utils import has_orga_permission
from dataclasses import dataclass
from django.db.models import QuerySet

    
@login_required
def pnj_form(request: HttpRequest, pk):
    url_validation = reverse('larp:pnj_form', kwargs={'pk': pk})
    instance = PnjInfos.objects.get(pk=pk)
    if request.method == "GET":
        form = PnjInfosForm(instance=instance, user=request.user)
        return render(request, 'larp/form.html', 
                {
                    'title': "Formulaire PNJ Faction",
                    'form': form,
                    'url_validation': url_validation})


    if request.method == "POST":
        form = PnjInfosForm(request.POST, instance=instance, user=request.user)
        if form.is_valid():
            form.save()

        return render(request, 'larp/form.html', 
                    {
                        "form": form,
                        'url_validation': url_validation})
    

@login_required
def create_pj(request: HttpRequest, inscription_id):
    url_validation = reverse('larp:create_pj', kwargs={'inscription_id':inscription_id})
    inscription = Inscription.objects.select_related("opus__larp").get(pk=inscription_id)
    larp = inscription.opus.larp
    if request.method == "GET":
        form = PjInfosForm(inscription=inscription, user=request.user)
        return render(request, 'larp/form.html', 
                {
                    'title': "Création de personnage",
                    'form': form,
                    'url_validation': url_validation})


    if request.method == "POST":
        form = PjInfosForm(request.POST, inscription=inscription, user=request.user)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.larp = larp
            instance.save()

            return redirect(reverse('larp:edit_pj', kwargs={'pjinfos_id':instance.pk}))

        return render(request, 'larp/form.html', 
                    {
                        "form": form,
                        'url_validation': url_validation})
    

@login_required
def orga_gn_list(request: HttpRequest):
    user_groups_id = request.user.groups.all().values_list('pk')
    user_orga_larps = Larp.objects.filter(orga_group_id__in=user_groups_id)
    context = {
        'larps': user_orga_larps
    }

    return render(request, 'larp/orga_gn_list.html', 
                context)


@login_required
def orga_gn(request: HttpRequest, larp_id):
    @dataclass
    class UserSheets:
        user: User
        access_type: str
        pnj_info: None|PnjInfos = None
        pj_infos: None|QuerySet|list[PjInfos] = None

    def list_sheets(larp, inscriptions: QuerySet|list[Inscription]):
        sheets = []
        pj_infos = PjInfos.objects.filter(larp=larp)
        pnj_infos = PnjInfos.objects.filter(larp=larp)
        for inscription in inscriptions:
            sheet = UserSheets(user=inscription.user,access_type=inscription.access_type)
            if 'PNJ' in inscription.access_type:
                sheet.pnj_info = pnj_infos.get(user=inscription.user)
            
            if inscription.access_type in ['PJ', 'PNJF']:
                sheet.pj_infos = pj_infos.filter(user=inscription.user)
            sheets.append(sheet)
        return sheets

    larp = Larp.objects.get(pk=larp_id)
    has_orga_permission(request.user, larp)
    last_opus = Opus.objects.filter(larp_id=larp_id).latest('created_at')
    inscriptions = Inscription.objects.filter(opus=last_opus)
    user_sheets = list_sheets(larp, inscriptions)
    context = {
        'opus': last_opus,
        'sheets': user_sheets
    }

    return render(request, 'larp/orga_gn.html', 
                context)


@login_required
def edit_pj(request: HttpRequest, pjinfos_id):
    url_validation = reverse('larp:edit_pj', kwargs={'pjinfos_id':pjinfos_id})
    pj_infos = PjInfos.objects.select_related('larp').get(pk=pjinfos_id)
    larp = pj_infos.larp
    if request.method == "GET":
        form = PjInfosForm(instance=pj_infos, larp=larp, user=request.user)
        return render(request, 'larp/form.html', 
                {
                    'title': "Création de personnage",
                    'form': form,
                    'url_validation': url_validation})


    if request.method == "POST":
        form = PjInfosForm(request.POST, instance=pj_infos, larp=larp, user=request.user)
        if form.is_valid():
            form.save()

        return render(request, 'larp/form.html', 
                    {
                        "form": form,
                        'url_validation': url_validation})
    
        
@login_required
def my_inscriptions(request: HttpRequest):
    inscriptions = Inscription.objects.select_related('opus__larp').filter(user=request.user)
    larps = {i.opus.larp for i in inscriptions}
    return render(request, 'larp/inscriptions.html', 
            {
                "larps": larps,
                'inscriptions': inscriptions})


@login_required
def profile(request: HttpRequest):
    # TODO: check que request.user.pk == user_pk ou que request.user est orga
    user_pk = request.GET.get('user_id', request.user.pk)

    requested_user = User.objects.get(pk=user_pk)
    context = {
        'title': "Mes informations",
        'requested_user': requested_user
    }
    profile = Profile.objects.get(user=requested_user)

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = ProfileForm(request.POST, instance=profile)
        # check whether it's valid:
        if form.is_valid():
            profile = form.save()
            profile.activated = True
            profile.save()
            context['form'] = form
            return render(request, 'larp/profile_form.html', 
            context)
        # If the form was invalid send the user back to fix it
        else:
            context['form'] = form
            return render(request, 'larp/profile_form.html', 
            context)
    # if a GET (or any other method) we'll create a blank form
    else:
        form = ProfileForm(instance=profile)
        context['form'] = form
        return render(request, 'larp/profile_form.html', context)
    

@login_required
def character_list(request: HttpRequest):
    from larp.utils import only_last_inscriptions
    #TODO : si les infos de profil (sécurité) ne sont pas remplies, redirection
    #TODO : test si on récupère bien seulement les dernières inscriptions par GN

    context = {
        'can_add_character': False
    }
    larp_inscriptions = only_last_inscriptions(request.user)

    context['larp_inscriptions'] = larp_inscriptions
    return render(request, 'larp/character_list.html', context)


# Permet un request GET parameter : inscription_id
@login_required
def test(request: HttpRequest):
    orga_groups = Group.objects.filter(larp__isnull=True)
    print(orga_groups)

        

@login_required
def view_pj(request: HttpRequest, pjinfos_id: int):
    """Display all information from a PjInfos instance in read-only format"""
    pj_infos = PjInfos.objects.select_related('faction', 'larp', 'user').get(pk=pjinfos_id)
    
    # Check if user has permission to view this character
    # User can view their own characters or be an orga for the larp
    if pj_infos.user != request.user:
        has_orga_permission(request.user, pj_infos.larp)
    
    # Get background choices for this character
    bg_choices = Character_Bg_choices.objects.filter(pjInfos=pj_infos).select_related('bgchoice__bg_step').order_by('step')
    
    context = {
        'title': f"Personnage: {pj_infos.name}",
        'pj_infos': pj_infos,
        'bg_choices': bg_choices,
        'larp': pj_infos.larp,
        'faction': pj_infos.faction,
        'user': pj_infos.user,
    }
    
    return render(request, 'larp/view_pj.html', context)


@login_required
def complete_bg(request: HttpRequest, pjinfo_id: int):
    pj_infos = PjInfos.objects.select_related('faction').get(pk=pjinfo_id, user=request.user)
    # Determine next step to display: count completed answers for this pj
    completed_steps = Character_Bg_choices.objects.filter(pjInfos=pj_infos).values_list('step', flat=True)
    next_step = (max(completed_steps) + 1) if completed_steps else 1

    # Find the BgStep for the player's faction and next step
    try:
        bg_step = BgStep.objects.get(faction=pj_infos.faction, step=next_step)
    except BgStep.DoesNotExist:
        # No more steps
        return render(request, 'larp/simple.html', {
            'title': "Background terminé",
            'text': "Vous avez répondu à toutes les questions disponibles."
        })

    choices_qs = BgChoice.objects.filter(bg_step=bg_step)

    url_validation = reverse('larp:complete_bg', kwargs={'pjinfo_id': pjinfo_id})

    if request.method == 'GET':
        form = BgAnswerForm(choices_qs=choices_qs)
        return render(request, 'larp/form.html', {
            'title': bg_step.short_name,
            'form': form,
            'question': bg_step.question,
            'url_validation': url_validation
        })

    if request.method == 'POST':
        form = BgAnswerForm(request.POST, choices_qs=choices_qs)
        if form.is_valid():
            selected_choice_id = int(form.cleaned_data['choice'])
            player_text = form.cleaned_data.get('player_text', '')
            selected_choice = choices_qs.get(pk=selected_choice_id)

            # Create or update the through model for this step
            Character_Bg_choices.objects.update_or_create(
                pjInfos=pj_infos,
                step=bg_step.step,
                defaults={'bgchoice': selected_choice, 'player_text': player_text}
            )

            # Check if this was the last step for this faction
            max_step_for_faction = BgStep.objects.filter(faction=pj_infos.faction).aggregate(
                max_step=models.Max('step')
            )['max_step']
            
            if bg_step.step >= max_step_for_faction:
                # This was the last step, mark background as completed
                pj_infos.bg_completed = True
                pj_infos.save()
                # Redirect to view_pj since background is now complete
                return redirect(reverse('larp:view_pj', kwargs={'pjinfos_id': pjinfo_id}))

            # Continue to next step if not completed
            return redirect(reverse('larp:complete_bg', kwargs={'pjinfo_id': pjinfo_id}))

        return render(request, 'larp/form.html', {
            'title': bg_step.short_name,
            'form': form,
            'question': bg_step.question,
            'url_validation': url_validation
        })