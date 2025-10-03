# cms_plugins.py
from djangocms_frontend.cms_plugins import CMSUIPlugin
from cms.plugin_pool import plugin_pool
from . import models, forms
    

@plugin_pool.register_plugin
class BackgroundMenuPlugin(CMSUIPlugin):
    model = models.BackgroundMenuPluginModel
    form = forms.BackgroundMenuPluginForm
    name = "Menu Image"
    render_template = "background_menu_plugin_template.html"
    allow_children = True
    child_classes = ['BackgroundLinkPlugin']

    fieldsets = [
        # All fields must be listed in the form, either as entangled or untangled
        # fields.
        (None, {
            "fields": [
                "max_height",
            ]
        }),
    ]

    def render(self, context, instance, placeholder):
        context = super().render(context, instance, placeholder)
        return context

@plugin_pool.register_plugin
class BackgroundLinkPlugin(CMSUIPlugin):
    model = models.BackgroundLinkPluginModel
    form = forms.BackgroundLinkPluginForm
    name = "Lien des échos"
    render_template = "background_link_plugin_template.html"
    require_parent = (
        True 
    )

    fieldsets = [
        # All fields must be listed in the form, either as entangled or untangled
        # fields.
        (None, {
            "fields": [
                "image",
                "link",
                "text"
            ]
        }),
    ]

    def render(self, context, instance, placeholder):
        context = super(BackgroundLinkPlugin, self).render(context, instance, placeholder)
        context.update({"image_url": instance.rel_image.canonical_url})
        return context
    