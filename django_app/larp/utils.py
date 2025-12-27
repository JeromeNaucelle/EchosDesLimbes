from django.http import HttpRequest
from larp import models as larp_models
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from reportlab.platypus import TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors


class CurrentInscription():
    def __init__(self, inscription: larp_models.Inscription):
        self.access_type = inscription.access_type
        self.created_at = inscription.created_at
        self.can_add_character = False
        self.larp_id = inscription.opus.larp.pk
        self.inscription_id = inscription.pk
        self.sheet_creation_opened = inscription.opus.larp.sheet_creation_opened

        if self.access_type == larp_models.AccessType.PJ or self.access_type == larp_models.AccessType.PNJF:
            self.pj_infos = larp_models.PjInfos.objects.filter(user=inscription.user, larp=inscription.opus.larp)

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
    return False


def orga_or_denied(request:HttpRequest, raise_exception=True):
    user = request.user
    
    if user.is_superuser:
        return True
    if request.session.get('is_orga', False):
        return True
    if raise_exception:
            raise PermissionDenied
    
PDF_TABLE_STYLE = TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])


def get_pdf_custom_styles(generic_styles):
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=generic_styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center alignment
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=generic_styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
    )
    indent_style = ParagraphStyle(
        'CustomIndentedParagraph',
        parent=generic_styles['Normal'],
        leftIndent=8
    )
    return title_style, heading_style, indent_style