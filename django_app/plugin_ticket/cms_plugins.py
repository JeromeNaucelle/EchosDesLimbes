# cms_plugins.py
from djangocms_frontend.cms_plugins import CMSUIPlugin
from cms.plugin_pool import plugin_pool
from . import models, forms
from larp.models import Ticket, Faction


@plugin_pool.register_plugin
class TicketPlugin(CMSUIPlugin):
    model = models.TicketPluginModel
    form = forms.TicketPluginForm
    name = "Ticket Plugin"
    #render_template = "ticket_plugin_template.html"

    fieldsets = [
        # All fields must be listed in the form, either as entangled or untangled
        # fields.
        (None, {
            "fields": [
                "ticket",
                "background",
                "text_color"
            ]
        }),
    ]

    def get_render_template(self, context, instance, placeholder):
        if context['ticket'].access_type == 'PNJV':
            return "ticket_pnjv_plugin_template.html"
        else:
            return "ticket_plugin_template.html"

    def render(self, context, instance, placeholder):
        ticket = Ticket.objects.select_related('opus__larp').get(pk=instance.ticket['pk'])
        factions = Faction.objects.filter(larp_id=ticket.opus.larp.pk)
        faction_name = ticket.opus.larp.factions_name
        if instance.rel_image:
            context.update({"background_img": instance.rel_image.canonical_url})

        if not hasattr(instance, 'text_color'):
            instance.text_color = "#000000"
        context.update({"ticket": ticket})
        context.update({"factions": factions})
        context.update({"faction_name": faction_name})
        context.update({"text_color": instance.text_color})
        return context