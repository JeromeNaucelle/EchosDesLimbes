# forms.py
from django import forms
from djangocms_frontend.models import FrontendUIItem
from djangocms_link.fields import LinkFormField
from entangled.forms import EntangledModelForm
from djangocms_frontend.contrib.image.fields import ImageFormField


class BackgroundMenuPluginForm(EntangledModelForm):
    class Meta:
        model = FrontendUIItem
        entangled_fields = {
            "config": [
                "max_height",
             ]
        }
        # untangled_fields = ("tag_type",)  # Only if you use the tag_type field

    max_height = forms.IntegerField(label="Hauteur max (en px)")

class BackgroundLinkPluginForm(EntangledModelForm):
    class Meta:
        model = FrontendUIItem
        entangled_fields = {
            "config": [
                "image",
                "link",
                "text"
             ]
        }
        # untangled_fields = ("tag_type",)  # Only if you use the tag_type field

    link = LinkFormField()
    image = ImageFormField()
    text = forms.CharField(label="Texte du lien")