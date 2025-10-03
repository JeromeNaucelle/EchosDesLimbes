from djangocms_frontend.models import FrontendUIItem
from djangocms_frontend.contrib.image.models import ImageMixin

class TicketPluginModel(ImageMixin, FrontendUIItem):
    class Meta:
        proxy = True  # MUST be a proxy model
        verbose_name = "Ticket Plugin"

    def short_description(self):
        #return f"'{self.field_name}'"
        return "Plugin de vente de ticket de GN"
    
    image_field = "background"
    