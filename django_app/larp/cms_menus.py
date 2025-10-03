from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from cms.menu_bases import CMSAttachMenu
from menus.base import NavigationNode
from menus.menu_pool import menu_pool
from .models import Larp


class LarpMenu(CMSAttachMenu):
    name = _("GNs menu")  # give the menu a name this is required.

    def get_nodes(self, request: HttpRequest):
        is_orga = request.session.get('is_orga', False)

        """
        This method is used to build the menu tree.
        """
        nodes = []
        node = NavigationNode(
                title='Mes Gns',
                url=reverse("larp:my_inscriptions"),
                id=1,  # unique id for this node within the menu
            )
        nodes.append(node)

        node = NavigationNode(
                title='Mon profil',
                url=reverse("larp:profile"),
                id=2,  # unique id for this node within the menu
            )
        nodes.append(node)

        node = NavigationNode(
                title='Mes personnages',
                url=reverse("larp:character_list"),
                id=3,  # unique id for this node within the menu
            )
        nodes.append(node)

        node = NavigationNode(
                title='Coin Orga',
                url=reverse("larp:orga_gn_list"),
                id=4,  # unique id for this node within the menu
            )
        if is_orga:
            nodes.append(node)
        
        return nodes


menu_pool.register_menu(LarpMenu)