# forms.py
from django import forms
from djangocms_frontend.models import FrontendUIItem
from entangled.forms import EntangledModelForm
from djangocms_frontend.contrib.image.fields import ImageFormField
from larp.models import Ticket

class TicketPluginForm(EntangledModelForm):
    class Meta:
        model = FrontendUIItem
        entangled_fields = {
            "config": [
                "background",
                "ticket",
                "text_color"
             ]
        }
        # untangled_fields = ("tag_type",)  # Only if you use the tag_type field
    background = ImageFormField()
    ticket = forms.ModelChoiceField(Ticket.objects.all())
    text_color = forms.CharField(max_length=10)