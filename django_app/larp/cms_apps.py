from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool


@apphook_pool.register  # register the application
class LarpApphook(CMSApp):
    app_name = "larp"
    name = "LARP admin"

    def get_urls(self, page=None, language=None, **kwargs):
        return ["larp.urls"]
    