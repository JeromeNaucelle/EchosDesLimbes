from djangocms_frontend.models import FrontendUIItem
from djangocms_frontend.contrib.image.models import ImageMixin
    

class BackgroundMenuPluginModel(FrontendUIItem):
    class Meta:
        proxy = True  # MUST be a proxy model
        verbose_name = "Menu image Plugin"

    

    def short_description(self):
        #return f"'{self.field_name}'"
        return "Prévu pour contenir des 'liens des échos'"


class BackgroundLinkPluginModel(ImageMixin, FrontendUIItem):
    class Meta:
        proxy = True  # MUST be a proxy model
        verbose_name = "Background link plugin"

    def short_description(self):
        #return f"'{self.field_name}'"
        return "Lien avec une image de fond"
    
    image_field = "image"
