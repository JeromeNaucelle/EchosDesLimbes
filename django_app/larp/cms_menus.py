from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from cms.menu_bases import CMSAttachMenu
from menus.base import NavigationNode, Modifier
from menus.menu_pool import menu_pool, MenuRenderer


class LarpNavExtender(Modifier):
    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        if post_cut:
            return nodes
        # rearrange the parent relations
        # Find home
        home = next((n for n in nodes if n.attr.get("is_home", False)), None)
        # Find nodes with NavExtenders
        exts = []
        for node in nodes:
            extenders = node.attr.get("navigation_extenders", None)
            if extenders:
                for ext in extenders:
                    if ext not in exts:
                        exts.append(ext)
                    # Link the nodes
                    for extnode in nodes:
                        if extnode.namespace == ext and not extnode.parent_id:
                            # if home has nav extenders but home is not visible
                            if node == home and not node.visible:
                                # extnode.parent_id = None
                                extnode.parent_namespace = None
                                extnode.parent = None
                            else:
                                extnode.parent_id = node.id
                                extnode.parent_namespace = node.namespace
                                extnode.parent = node
                                node.children.append(extnode)
        removed = []

        if breadcrumb:
            # if breadcrumb and home not in navigation add node
            if breadcrumb and home and not home.visible:
                home.visible = True
                if request.path_info == home.get_absolute_url():
                    home.selected = True
                else:
                    home.selected = False
        # remove all nodes that are nav_extenders and not assigned
        for node in removed:
            nodes.remove(node)
        return nodes

class LarpMenuRenderer(MenuRenderer):
    def __init__(self, pool, request):
        super(LarpMenuRenderer, self).__init__(pool, request)
        self.menus = {'LarpMenu': pool.get_registered_menus()['LarpMenu']}

    @property
    def cache_key(self):
        prefix = 'larp_'

        key = f"{prefix}menu_nodes_{self.request_language}_{self.site.pk}"

        if self.request.user.is_authenticated:
            key += f"_{self.request.user.pk}_user"

        if self.edit_or_preview:
            key += ':edit'
        else:
            key += ':public'
        return key
    
    def apply_modifiers(self, nodes, namespace=None, root_id=None, post_cut=False, breadcrumb=False):
        if not post_cut:
            nodes = self._mark_selected(nodes)

        # Only fetch modifiers when they're needed.
        # We can do this because unlike menu classes,
        # modifiers can't change on a request basis.
        modifier = LarpNavExtender(self)
        nodes = modifier.modify(
            self.request, nodes, namespace, root_id, post_cut, breadcrumb)
        return nodes
    




class LarpMenu(CMSAttachMenu):
    name = _("GNs menu")  # give the menu a name this is required.

    def get_nodes(self, request: HttpRequest):
        is_orga = request.session.get('is_orga', False)

        """
        This method is used to build the menu tree.
        """
        nodes = []

        node = NavigationNode(
                title=f"{request.user.username}",
                url=reverse("larp:profile", kwargs={'user_id': request.user.pk}),
                id=1,  # unique id for this node within the menu
            )
        node.level = 0
        nodes.append(node)

        node = NavigationNode(
                title='Mon profil',
                url=reverse("larp:profile", kwargs={'user_id': request.user.pk}),
                id=2,  # unique id for this node within the menu
                parent_id=1
            )
        nodes.append(node)

        node = NavigationNode(
                title='Mes personnages',
                url=reverse("larp:character_list"),
                id=3,  # unique id for this node within the menu
                parent_id=1
            )
        nodes.append(node)

        node = NavigationNode(
                title='Coin Orga',
                url=reverse("larp:orga_gn_list"),
                id=4,  # unique id for this node within the menu
                parent_id=1
            )
        if is_orga:
            nodes.append(node)
        
        node = NavigationNode(
                title='Mes achats',
                url=reverse("payments:purchase-list"),
                id=5,  # unique id for this node within the menu
                parent_id=1
            )
        nodes.append(node)

        return nodes

menu_pool.register_menu(LarpMenu)