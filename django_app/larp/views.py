from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http.request import HttpRequest
from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Q
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.units import mm
from io import BytesIO
from django.db import transaction
from django_htmx.http import HttpResponseClientRedirect
from django.contrib import messages

from .models import Profile, Inscription, PnjInfos,PjInfos, Larp, Opus, BgStep, BgChoice, Character_Bg_choices, Faction
from larp.forms import PjDocumentForm, ProfileForm, PnjInfosForm, PjInfosForm, BgAnswerForm, BgStepForm, BgChoiceForm, PjStatusForm, CharacterBgTextForm
from larp.utils import has_orga_permission, orga_or_denied, get_pdf_custom_styles, PDF_TABLE_STYLE
from django.core.exceptions import BadRequest, PermissionDenied

    
@login_required
def pnj_form(request: HttpRequest, pk):
    url_validation = reverse('larp:pnj_form', kwargs={'pk': pk})
    instance = PnjInfos.objects.get(pk=pk)
    if request.method == "GET":
        form = PnjInfosForm(instance=instance, user=request.user)
        return render(request, 'larp/pnj_form.html', 
                {
                    'title': "Formulaire PNJ",
                    'form': form,
                    'url_validation': url_validation})


    if request.method == "POST":
        form = PnjInfosForm(request.POST, instance=instance, user=request.user)
        if form.is_valid():
            form.save()
            return redirect(reverse('larp:view_pnj', kwargs={'pnjinfos_id': instance.pk}))

        return render(request, 'larp/pnj_form.html', 
                    {
                        'title': "Formulaire PNJ",
                        "form": form,
                        'url_validation': url_validation})
    

@login_required
def create_pj(request: HttpRequest, inscription_id):
    url_validation = reverse('larp:create_pj', kwargs={'inscription_id':inscription_id})
    inscription = Inscription.objects.select_related("opus__larp").get(pk=inscription_id)
    larp = inscription.opus.larp
    if request.method == "GET":
        form = PjInfosForm(inscription=inscription, user=request.user)
        return render(request, 'larp/create_pj.html', 
                {
                    'larp': larp,
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

        return render(request, 'larp/create_pj.html', 
                    {
                        'larp': larp,
                        "form": form,
                        'url_validation': url_validation})
    

@login_required
def edit_bg_choice(request: HttpRequest, bgchoice_id: int):
    charac_choice = Character_Bg_choices.objects.select_related('pjInfos__larp', 'pjInfos__user').get(pk=bgchoice_id)
    larp = charac_choice.pjInfos.larp
    if request.user.pk != charac_choice.pjInfos.user.pk:
        has_orga_permission(request.user, larp)

    if request.method == "GET":
        form = CharacterBgTextForm(instance=charac_choice)

    elif request.method == "POST":
        form = CharacterBgTextForm(request.POST, instance=charac_choice)
        if form.is_valid():
            form.save()

    else:
        raise BadRequest("Method not allowed")
    
    context = {
        'bg_choice': charac_choice,
        'form': form
        }
    return render(request, 'larp/bg_choice.html', 
                context)

@login_required
def player_document(request: HttpRequest, pjinfos_id: int):
    pj_infos = PjInfos.objects.select_related('larp').get(pk=pjinfos_id)
    has_orga_permission(request.user, pj_infos.larp)

    if request.method == "POST":
        document_form = PjDocumentForm(request.POST)
        if document_form.is_valid():
            pj_doc = document_form.save(commit=False)
            pj_doc.pj = pj_infos
            pj_doc.save()

    elif request.method == "DELETE":
        document_id = request.GET['document_id']
        document = pj_infos.documents.get(pk=document_id)
        document.delete()

    else:
        raise BadRequest("Method not allowed")

    
    document_form = PjDocumentForm()
    context = {
        'is_orga': True,
        'pj_infos': pj_infos,
        'document_form': document_form
        }
    return render(request, 'larp/view_pj.html#pj-documents', 
                context)

@login_required
def orga_gn_list(request: HttpRequest):
    if request.user.is_superuser:
        user_orga_larps = Larp.objects.all()
    else:
        user_groups_id = request.user.groups.all().values_list('pk')
        user_orga_larps = Larp.objects.filter(orga_group_id__in=user_groups_id)
    context = {
        'larps': user_orga_larps
    }

    return render(request, 'larp/orga/orga_gn_list.html', 
                context)


def orga_gn_pnjv(request: HttpRequest, last_opus, larp, factions):
    pnjv_user_ids = Inscription.objects.filter(opus=last_opus, access_type='PNJV').values_list('user_id', flat=True)
    pnjv_list = list(PnjInfos.objects.filter(larp=larp, user_id__in=pnjv_user_ids).select_related('user').order_by('user__last_name', 'user__first_name'))

    context = {
        'larp': larp,
        'opus': last_opus,
        'pnjv_list': pnjv_list,
        'factions': factions,
        'selected_faction': 'PNJV',
    }

    return render(request, 'larp/orga/orga_gn.html', context)


@login_required
def orga_gn(request: HttpRequest, larp_id):
    from .models import Faction  # local import to avoid circulars in headings
    larp = Larp.objects.get(pk=larp_id)
    has_orga_permission(request.user, larp)
    try:
        last_opus = Opus.objects.filter(larp_id=larp_id).latest('created_at')
    except Opus.DoesNotExist:
        return render(request, 'larp/simple.html', {'message': "Erreur : aucun opus créé pour ce GN"})
    factions = Faction.objects.filter(larp=larp).order_by('name')


    # Get selected faction from query parameters
    selected_faction_id = request.GET.get('faction')
    selected_faction = None
    if selected_faction_id:
        if selected_faction_id == 'PNJV':
            return orga_gn_pnjv(request, last_opus, larp, factions)
        else:
            try:
                selected_faction = Faction.objects.get(pk=selected_faction_id, larp=larp)
            except Faction.DoesNotExist:
                selected_faction = None

        
    factions_to_process = factions if selected_faction is None else [selected_faction]
    
    # Get all inscriptions for the latest opus
    inscriptions = Inscription.objects.filter(opus=last_opus).select_related('user', 'faction')
    
    # Create faction data with both PJ and PNJF lists
    faction_data = []
    
    for faction in factions_to_process:
        # Pure PJ users (access_type = 'PJ')
        pj_users = inscriptions.filter(faction=faction, access_type='PJ').values_list('user_id', flat=True)
        pj_list = list(PjInfos.objects.filter(larp=larp, faction=faction, user_id__in=pj_users).order_by('name'))
        
        # PNJF users (access_type = 'PNJF') - have both PJ and PNJ sheets
        pnjf_users = inscriptions.filter(faction=faction, access_type='PNJF').values_list('user_id', flat=True)
        pnjf_list = []
        for user_id in pnjf_users:
            try:
                pj_infos = PjInfos.objects.get(larp=larp, faction=faction, user_id=user_id)
                pnj_infos = PnjInfos.objects.get(larp=larp, user_id=user_id)
                pnjf_list.append({
                    'user': pj_infos.user,
                    'pj_infos': pj_infos,
                    'pnj_infos': pnj_infos
                })
            except (PjInfos.DoesNotExist, PnjInfos.DoesNotExist):
                # Skip if either sheet is missing
                continue
        
        faction_data.append({
            'faction': faction,
            'pj_list': pj_list,
            'pnjf_list': pnjf_list
        })

    # PNJV: PNJ volant have no faction; take users with PNJV inscription on latest opus
    pnjv_user_ids = Inscription.objects.filter(opus=last_opus, access_type='PNJV').values_list('user_id', flat=True)
    pnjv_list = list(PnjInfos.objects.filter(larp=larp, user_id__in=pnjv_user_ids).select_related('user').order_by('user__last_name', 'user__first_name'))

    context = {
        'larp': larp,
        'opus': last_opus,
        'faction_data': faction_data,
        'pnjv_list': pnjv_list,
        'factions': factions,
        'selected_faction': selected_faction,
    }

    return render(request, 'larp/orga/orga_gn.html', context)


@login_required
def change_pnj_status(request: HttpRequest, pnjinfos_id):
    from django.core.exceptions import BadRequest, PermissionDenied
    pnj_infos = PnjInfos.objects.select_related('larp').get(pk=pnjinfos_id)

    if not request.method == "POST":
        raise BadRequest("Method not allowed")
    
    completed = bool(request.POST.get('completed', 0))    
    is_orga = has_orga_permission(request.user, pnj_infos.larp, False)
    if not is_orga:
        if request.user.pk != pnj_infos.user.pk or \
            completed is not True:
            raise PermissionDenied()
    
    pnj_infos.completed = completed
    pnj_infos.save()
    return redirect(reverse('larp:view_pnj', kwargs={'pnjinfos_id': pnjinfos_id}))

@login_required
def change_pj_status(request: HttpRequest, pjinfos_id):
    pj_infos = PjInfos.objects.select_related('larp').get(pk=pjinfos_id)

    if not request.method == "POST":
        raise BadRequest("Method not allowed")
    
    status = request.POST.get('status', '')
    if status not in list(PjInfos.SHEET_STATUS.__members__.keys()):
        raise BadRequest("Unknown status")
    
    is_orga = has_orga_permission(request.user, pj_infos.larp, False)
    if not is_orga:
        if request.user.pk != pj_infos.user.pk or \
            status != PjInfos.SHEET_STATUS.PLAYER_VALIDATED.name:
            raise PermissionDenied()
    
    pj_infos.status = status
    pj_infos.save()
    return redirect(reverse('larp:view_pj', kwargs={'pjinfos_id': pjinfos_id}))

@login_required
def edit_pj(request: HttpRequest, pjinfos_id):
    url_validation = reverse('larp:edit_pj', kwargs={'pjinfos_id':pjinfos_id})
    pj_infos = PjInfos.objects.select_related('larp').get(pk=pjinfos_id)
    larp = pj_infos.larp
    if request.method == "GET":
        form = PjInfosForm(instance=pj_infos, larp=larp, user=request.user)
        return render(request, 'larp/edit_pj.html', 
                {
                    'title': "Création de personnage",
                    'form': form,
                    'url_validation': url_validation})


    if request.method == "POST":
        form = PjInfosForm(request.POST, instance=pj_infos, larp=larp, user=request.user)
        if form.is_valid():
            instance = form.save()
            return redirect(reverse('larp:view_pj', kwargs={'pjinfos_id': instance.pk}))

        return render(request, 'larp/edit_pj.html', 
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
def bg_choice_requisit(request: HttpRequest, bg_choice_id: int):
    bg_choice = get_object_or_404(BgChoice.objects.select_related('bg_step__faction__larp'), pk=bg_choice_id)
    has_orga_permission(request.user, bg_choice.bg_step.faction.larp)
    bg_steps = BgStep.objects.filter(faction=bg_choice.bg_step.faction, step__lt=bg_choice.bg_step.step)


    template_name = "larp/orga/bg_choice_requisit.html"
    if request.htmx:
        if request.method == 'POST':
            template_name += "#choice-list"
            step_id = int(request.POST['step_id'])
            choices = BgChoice.objects.filter(bg_step_id=step_id)
        if request.method == 'DELETE':
            bg_choice.requisit = None
            bg_choice.save()
            return HttpResponseClientRedirect(reverse('larp:bg_choices', kwargs={'bg_step_id': bg_choice.bg_step.pk}))
    else:
        if bg_choice.requisit:
            choices = BgChoice.objects.filter(bg_step_id=bg_choice.requisit.bg_step_id)
        else:
            choices = []

        if request.method == 'POST':
            choice_id = int(request.POST['choice_id'])
            bg_choice.requisit_id = choice_id
            bg_choice.save()
            return redirect(reverse('larp:bg_choices', kwargs={'bg_step_id': bg_choice.bg_step.pk}))


    return render(request, template_name, 
            {
                "bg_choice": bg_choice,
                "bg_steps": bg_steps,
                "choices": choices
            })

@login_required
def bg_choices(request: HttpRequest, bg_step_id: int):
    bg_step = get_object_or_404(BgStep.objects.select_related('faction__larp'), pk=bg_step_id)
    has_orga_permission(request.user, bg_step.faction.larp)
    bg_choices = BgChoice.objects.filter(bg_step=bg_step)
    template = 'larp/orga/bg_choices.html'
    action = 'add-choice'

    if request.htmx:
        if request.method == 'POST':
            template += '#choice-form'
            action = 'edit-choice'
            current_choice = BgChoice.objects.get(pk=request.POST['choice_id'])
            form = BgChoiceForm(action=action, instance=current_choice)
        if request.method == 'DELETE':
            current_choice = BgChoice.objects.get(pk=request.GET['choice_id'])
            current_choice.delete()
            return HttpResponseClientRedirect(reverse('larp:bg_choices', kwargs={'bg_step_id': bg_step_id}))

    else:
        if request.method == 'GET':
            form = BgChoiceForm(action=action)

        if request.method == 'POST':
            if request.POST['action'] == 'edit-choice':
                current_choice = BgChoice.objects.get(pk=request.POST['choice_id'])
                form = BgChoiceForm(request.POST, action=action, instance=current_choice)
                if form.is_valid():
                    form.save()
                # On retourne un formulaire vide s'il est valide
                    form = BgChoiceForm(action='add-choice')
            else:
                form = BgChoiceForm(request.POST, action=action)
                if form.is_valid():
                    choice = form.save(commit=False)
                    choice.bg_step = bg_step
                    choice.save()
                    form = BgChoiceForm(action='add-choice')

    return render(request, template, 
            {
                "action": action,
                "bg_step": bg_step,
                "form": form,
                "bg_choices": bg_choices,
            })



@transaction.atomic
def bg_step_change_nb(request: HttpRequest, faction_id: int):
    faction = get_object_or_404(Faction.objects.select_related('larp'), pk=faction_id)
    has_orga_permission(request.user, faction.larp)
    faction_steps = BgStep.objects.filter(faction_id=faction_id)
    action = request.GET.get('action', None)
    bg_step_id = request.GET.get('step_id', None)
    bg_step = faction_steps.get(pk=bg_step_id)

    if action == 'up':
        previous_step = faction_steps.get(step=bg_step.step-1)
        previous_step.step = previous_step.step + 1
        previous_step.save()
        bg_step.step = bg_step.step - 1
    if action == 'down':
        next_step = faction_steps.get(step=bg_step.step+1)
        next_step.step = next_step.step - 1
        next_step.save()
        bg_step.step = bg_step.step + 1

    bg_step.save()

    return redirect(reverse('larp:bg_steps', kwargs={'faction_id': faction_id}))

@login_required
def bg_steps(request: HttpRequest, faction_id: int):
    faction = get_object_or_404(Faction.objects.select_related('larp'), pk=faction_id)
    has_orga_permission(request.user, faction.larp)
    template = 'larp/orga/bg_steps.html'
    action = 'add-step'

    if request.htmx:
        if request.method == 'POST':
            template += '#step-form'
            action = 'edit-step'
            current_step = BgStep.objects.get(pk=request.POST['step_id'])
            form = BgStepForm(action=action, instance=current_step)
        if request.method == 'DELETE':
            current_step = BgStep.objects.get(pk=request.GET['step_id'])
            current_step.delete()
            return HttpResponseClientRedirect(reverse('larp:bg_steps', kwargs={'faction_id': faction_id}))


    else:
        if request.method == 'GET':
            form = BgStepForm(action=action)

        if request.method == 'POST':
            if request.POST['action'] == 'edit-step':
                current_step = BgStep.objects.get(pk=request.POST['step_id'])
                form = BgStepForm(request.POST, action=action, instance=current_step)
                if form.is_valid():
                    form.save()
                # On retourne un formulaire vide s'il est valide
                    form = BgStepForm(action='add-step')


            else:
                current_step_nb = BgStep.objects.filter(faction=faction).count()
                form = BgStepForm(request.POST, action=action)
                if form.is_valid():
                    step = form.save(commit=False)
                    step.faction = faction
                    step.step = current_step_nb + 1
                    step.save()
                    # On retourne un formulaire vide s'il est valide
                    form = BgStepForm(action='add-step')

    current_steps = BgStep.objects.filter(faction=faction).order_by('step')
    return render(request, template,
            {
                "action": action,
                "form": form,
                "faction": faction,
                "current_steps": current_steps,
            })


@login_required
def profile(request: HttpRequest, user_id: int):
    if not request.user.pk == user_id:
        orga_or_denied(request)

    requested_user = User.objects.get(pk=user_id)
    context = {
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
            return render(request, 
                            'larp/profile_form.html', 
                            context)
        # If the form was invalid send the user back to fix it
        else:
            context['form'] = form
            return render(request, 
                          'larp/profile_form.html', 
                            context)
    # if a GET (or any other method) we'll create a blank form
    else:
        form = ProfileForm(instance=profile)
        context['form'] = form
        return render(request, 'larp/profile_form.html', context)
    

@login_required
def view_profile_pdf(request: HttpRequest, user_id: int):
    if not request.user.pk == user_id:
        orga_or_denied(request)

    user = User.objects.get(pk=user_id)
    profile = Profile.objects.get(user=user)
    
    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="fiche_sécurité_{user.first_name}_{user.last_name}.pdf"'
    
    # Create PDF document
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style, heading_style, indent_style = get_pdf_custom_styles(styles)
    
    # Build PDF content
    story = []
    
    # Title
    story.append(Paragraph(f"Fiche Sécurité : {user.first_name} {user.last_name}", title_style))
    
    # General Information
    story.append(Paragraph("Profil utilisateur", heading_style))

    birthdate = profile.birthdate.strftime("%d / %m / %Y")
    story.append(Paragraph(f"<b>Date de naissance : </b> {birthdate}", styles['Normal']))

    story.append(Spacer(1, 12))
    pseudos = profile.pseudos.replace('\n', '<br/>')
    story.append(Paragraph(f"<b>Pseudo sur les réseaux sociaux : </b>", styles['Normal']))
    story.append(Paragraph(pseudos, indent_style))

    story.append(Spacer(1, 20))

    # Security informations
    story.append(Paragraph("Informations de sécurité", heading_style))

    story.append(Paragraph(f"<b>Régime alimentaire, allergie ou autre élément de santé : </b>", styles['Normal']))
    story.append(Paragraph(profile.food.replace('\n', '<br/>'), indent_style))

    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Personnes avec qui je ne souhaite pas jouer : </b>", styles['Normal']))
    story.append(Paragraph(profile.unwanted_people.replace('\n', '<br/>'), indent_style))
    
    story.append(Spacer(1, 12))
    xp_gn = Profile.XP_GN[profile.xp_gn].value
    story.append(Paragraph(f"<b>Expérience GNistique : </b> {xp_gn}", styles['Normal']))

    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Phobies : </b>", styles['Normal']))
    story.append(Paragraph(profile.fears.replace('\n', '<br/>'), indent_style))

    story.append(Spacer(1, 12))
    triggers = [str(t) for t in profile.triggers.all()]
    story.append(Paragraph(f"<b>Désirs de non jeu / triggers : </b>", styles['Normal']))
    story.append(Paragraph('<br/>'.join(triggers), indent_style))

    story.append(Spacer(1, 20))
    story.append(Paragraph("Contacts d'urgence", heading_style))
    story.append(Paragraph(profile.emergency_contact.replace('\n', '<br/>'), indent_style))
    
        # Build PDF
    doc.build(story)
    
    # Get PDF content
    pdf_content = buffer.getvalue()
    buffer.close()
    
    response.write(pdf_content)
    return response
    

@login_required
def character_list(request: HttpRequest):
    from larp.utils import only_last_inscriptions
    if request.user.profile.activated is False:
        messages.error(request, 'Merci de commencer par remplir vos informations de sécurité avant de de créer vos fiches PJ/PNJ')
        return redirect(reverse('larp:profile', kwargs={'user_id': request.user.pk}))

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
    is_orga = has_orga_permission(request.user, pj_infos.larp, False)
    if pj_infos.user != request.user and not is_orga:
        raise PermissionDenied()
    
    # Get background choices for this character
    bg_choices = Character_Bg_choices.objects.filter(pjInfos=pj_infos).select_related('bgchoice__bg_step').order_by('step')
    
    context = {
        'title': f"Personnage: {pj_infos.name}",
        'status_form': PjStatusForm(instance=pj_infos),
        'pj_infos': pj_infos,
        'bg_choices': bg_choices,
        'larp': pj_infos.larp,
        'faction': pj_infos.faction,
        'user': pj_infos.user,
        'is_orga': is_orga, 
        'document_form': PjDocumentForm()
    }
    
    return render(request, 'larp/view_pj.html', context)


@login_required
def view_pj_pdf(request: HttpRequest, pjinfos_id: int):
    """Generate PDF export of PjInfos information"""
    pj_infos = PjInfos.objects.select_related('faction', 'larp', 'user').get(pk=pjinfos_id)
    
    # Check if user has permission to view this character
    if pj_infos.user != request.user:
        has_orga_permission(request.user, pj_infos.larp)
    
    # Get background choices for this character
    bg_choices = Character_Bg_choices.objects.filter(pjInfos=pj_infos).select_related('bgchoice__bg_step').order_by('step')
    
    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="personnage_{pj_infos.name}_{pj_infos.larp.name}.pdf"'
    
    # Create PDF document
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style, heading_style, indent_style = get_pdf_custom_styles(styles)
    
    # Build PDF content
    story = []
    
    # Title
    story.append(Paragraph(f"Fiche Personnage: {pj_infos.name}", title_style))

    # Contact Orga
    story.append(Paragraph("Contact Orga", heading_style))
    story.append(Paragraph(pj_infos.faction.orga_contact.replace('\n', '<br/>'), indent_style))
    
    # General Information
    story.append(Paragraph("Informations générales", heading_style))
    
    general_data = [
        ['Joueur :', f"{pj_infos.user.first_name} {pj_infos.user.last_name}"],
        ["Nom d'utilisateur :", f"{pj_infos.user.username}"],
        [pj_infos.larp.factions_name, pj_infos.faction.name],
        ['Préférence émotionnelle :', pj_infos.get_emotions_display()],
    ]
    
    general_table = Table(general_data, colWidths=[60*mm,100*mm])
    general_table.setStyle(PDF_TABLE_STYLE)
    
    story.append(general_table)
    story.append(Spacer(1, 20))
    
    # Skills
    story.append(Paragraph("Compétences", heading_style))
    story.append(Paragraph(f"<b>Compétences actuelles:</b>", styles['Normal']))
    story.append(Paragraph(pj_infos.skills.replace('\n', '<br/>'), indent_style))
    
    if pj_infos.last_learned:
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Dernière compétence apprise:</b> {pj_infos.last_learned}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Objectives
    if pj_infos.objectives:
        story.append(Paragraph("Objectifs de jeu", heading_style))
        story.append(Paragraph(pj_infos.objectives.replace('\n', '<br/>'), indent_style))
        story.append(Spacer(1, 20))
    
    # Background Choices
    if bg_choices:
        story.append(Paragraph("Choix de background", heading_style))
        
        for bg_choice in bg_choices:
            story.append(Paragraph(f"<b>Étape {bg_choice.step}: </b><i>{bg_choice.bgchoice.bg_step.question}</i>", styles['Normal']))
            story.append(Spacer(1, 6))
            
            choice_text = bg_choice.bgchoice.text or bg_choice.bgchoice.short_name
            story.append(Paragraph(f"{choice_text}", styles['Normal']))
            
            if bg_choice.player_text:
                story.append(Spacer(1, 6))
                story.append(Paragraph(f"<b>Commentaire du joueur:</b>", styles['Normal']))
                story.append(Paragraph(bg_choice.player_text.replace('\n', '<br/>'), indent_style))
            
            story.append(Spacer(1, 15))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF content
    pdf_content = buffer.getvalue()
    buffer.close()
    
    response.write(pdf_content)
    return response


@login_required
def view_pnj(request: HttpRequest, pnjinfos_id: int):
    """Display all information from a PnjInfos instance in read-only format"""
    pnj_infos = PnjInfos.objects.select_related('larp', 'user').get(pk=pnjinfos_id)
    last_inscription = Inscription.objects.\
                            select_related('opus__larp').\
                            filter(user=pnj_infos.user, opus__larp=pnj_infos.larp).\
                            latest('created_at')
    
    # Check if user has permission to view this PNJ info
    # User can view their own PNJ info or be an orga for the larp
    if pnj_infos.user != request.user:
        has_orga_permission(request.user, pnj_infos.larp)
    
    context = {
        'title': f"Fiche PNJ: {pnj_infos.user.first_name} {pnj_infos.user.last_name}",
        'pnj_infos': pnj_infos,
        'larp': pnj_infos.larp,
        'user': pnj_infos.user,
        'inscription': last_inscription
    }
    
    return render(request, 'larp/view_pnj.html', context)


@login_required
def view_pnj_pdf(request: HttpRequest, pnjinfos_id: int):
    """Generate PDF export of PnjInfos information"""
    pnj_infos = PnjInfos.objects.select_related('larp', 'user').get(pk=pnjinfos_id)
    
    # Check if user has permission to view this PNJ info
    if pnj_infos.user != request.user:
        has_orga_permission(request.user, pnj_infos.larp)

    inscription = Inscription.objects.\
                            select_related('opus__larp').\
                            filter(user=pnj_infos.user, opus__larp=pnj_infos.larp).\
                            latest('created_at')
    
    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="pnj_{pnj_infos.user.first_name}_{pnj_infos.user.last_name}_{pnj_infos.larp.name}.pdf"'
    
    # Create PDF document
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style, heading_style, indent_style = get_pdf_custom_styles(styles)
    
    # Build PDF content
    story = []
    
    # Title
    story.append(Paragraph(f"Fiche PNJ: {pnj_infos.user.first_name} {pnj_infos.user.last_name}", title_style))

    # Contact Orga
    story.append(Paragraph("Contact Orga", heading_style))
    if inscription.access_type == 'PNJV':
        infos_orga = pnj_infos.larp.pnjv_orga_contact
    else:
        infos_orga = inscription.faction.orga_contact
    story.append(Paragraph(infos_orga.replace('\n', '<br/>'), indent_style))
    
    # General Information
    story.append(Paragraph("Informations générales", heading_style))
    
    general_data = [
        ['Joueur :', f"{pnj_infos.user.first_name} {pnj_infos.user.last_name}"],
        ["Nom d'utilisateur :", f"{pnj_infos.user.username}"],
        ['Préférence horaire :', pnj_infos.get_prefered_time_display() if pnj_infos.prefered_time else 'Non spécifié'],
        ['Action de nuit :', 'Oui' if pnj_infos.nigth_action else 'Non' if pnj_infos.nigth_action is not None else 'Non spécifié'],
    ]
    
    general_table = Table(general_data, colWidths=[60*mm,100*mm])
    general_table.setStyle(PDF_TABLE_STYLE)
    
    story.append(general_table)
    story.append(Spacer(1, 20))
    
    # Preferences
    story.append(Paragraph("Préférences de jeu", heading_style))
    
    preferences_data = [
        ['Logistique (0) vs Rôles (5) :', pnj_infos.get_logistic_or_role_display() if pnj_infos.logistic_or_role is not None else 'Non spécifié'],
        ['Niveau d\'importance (0-5) :', pnj_infos.get_importance_display() if pnj_infos.importance is not None else 'Non spécifié'],
    ]
    
    preferences_table = Table(preferences_data, colWidths=[60*mm,100*mm])
    preferences_table.setStyle(PDF_TABLE_STYLE)
    
    story.append(preferences_table)
    story.append(Spacer(1, 20))
    
    # Talents
    if pnj_infos.talent:
        story.append(Paragraph("Talents particuliers", heading_style))
        story.append(Paragraph(pnj_infos.talent.replace('\n', '<br/>'), indent_style))
        story.append(Spacer(1, 20))
    
    # Organizer Information
    if pnj_infos.info_orga:
        story.append(Paragraph("Informations pour l'organisation", heading_style))
        story.append(Paragraph(pnj_infos.info_orga.replace('\n', '<br/>'), indent_style))
        story.append(Spacer(1, 20))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF content
    pdf_content = buffer.getvalue()
    buffer.close()
    
    response.write(pdf_content)
    return response


@login_required
def complete_bg(request: HttpRequest, pjinfos_id: int):
    pj_infos = PjInfos.objects.select_related('faction').get(pk=pjinfos_id, user=request.user)
    # Determine next step to display: count completed answers for this pj
    completed_steps = Character_Bg_choices.objects.filter(pjInfos=pj_infos).values_list('step', flat=True)
    next_step = (max(completed_steps) + 1) if completed_steps else 1

    # Find the BgStep for the player's faction and next step
    try:
        bg_step = BgStep.objects.get(faction=pj_infos.faction, step=next_step)
    except BgStep.DoesNotExist:
        return redirect(reverse('larp:view_pj', kwargs={'pjinfos_id': pjinfos_id}))

    # Get all choices for this step
    all_choices_qs = BgChoice.objects.filter(bg_step=bg_step)
    
    # Get choices already made by this character
    character_choices = Character_Bg_choices.objects.filter(pjInfos=pj_infos).values_list('bgchoice', flat=True)
    
    # Filter choices based on requisit: only show choices with no requisit or where the requisit has been chosen
    choices_qs = all_choices_qs.filter(
        Q(requisit__isnull=True) | Q(requisit__in=character_choices)
    )

    url_validation = reverse('larp:complete_bg', kwargs={'pjinfos_id': pjinfos_id})

    if request.method == 'GET':
        form = BgAnswerForm(choices_qs=choices_qs)
        return render(request, 'larp/complete_bg.html', {
            'pj_infos': pj_infos,
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
                return redirect(reverse('larp:view_pj', kwargs={'pjinfos_id': pjinfos_id}))

            # Continue to next step if not completed
            return redirect(reverse('larp:complete_bg', kwargs={'pjinfos_id': pjinfos_id}))

        return render(request, 'larp/complete_bg.html', {
            'pj_infos': pj_infos,
            'title': bg_step.short_name,
            'form': form,
            'question': bg_step.question,
            'url_validation': url_validation
        })