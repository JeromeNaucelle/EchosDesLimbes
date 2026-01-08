from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from . import models


# Register your models here.
admin.site.register(models.Larp)
admin.site.register(models.Trigger)
admin.site.register(models.Profile)

class FactionAdmin(admin.ModelAdmin):
    # a list of displayed columns name.
    list_select_related = ["larp"]
    list_display = ['name','larp']
    search_fields = ('name','larp__name')

admin.site.register(models.Faction, FactionAdmin)


class OpusAdmin(admin.ModelAdmin):
    list_select_related = ["larp"]
    list_display = ['name','larp_name']
    exclude=('pj_form', 'pnj_form', )


admin.site.register(models.Opus, OpusAdmin)

class TicketAdmin(admin.ModelAdmin):
    # a list of displayed columns name.
    list_select_related = ["opus", "opus__larp"]
    list_display = ['larp_name','opus', 'price', 'access_type']
    
    @admin.display(description= "Opus")
    def opus(self, Ticket):
        return Ticket.opus.name

admin.site.register(models.Ticket, TicketAdmin)


class PjInfosAdmin(admin.ModelAdmin):
    # a list of displayed columns name.
    list_select_related = ["larp", "faction"]
    list_display = ['user','name', 'larp_name', 'faction', 'status']
    search_fields = ('user', 'name')

admin.site.register(models.PjInfos, PjInfosAdmin)

class PnjInfosAdmin(admin.ModelAdmin):
    # a list of displayed columns name.
    list_select_related = ["larp"]
    list_display = ['user', 'larp_name', 'completed']
    search_fields = ('user',)

admin.site.register(models.PnjInfos, PnjInfosAdmin)


class AccesTypeClasseFilter(SimpleListFilter):
    title = "Type d'accès"  # a label for our filter
    parameter_name = "type"  # you can put anything here

    def lookups(self, request, model_admin):
        # This is where you create filter options; 
        choices = models.AccessType.choices
        return choices

    def queryset(self, request, queryset):
        # This is where you process parameters selected by use via filter options:
        if self.value() is None:
            return queryset.all()
        access_type = str(self.value())
        return queryset.filter(access_type__iexact=access_type)

class InscriptionAdmin(admin.ModelAdmin):
    # a list of displayed columns name.
    list_select_related = ["opus", "opus__larp", "faction"]
    list_display = ['user','larp_name', 'opus', 'faction', 'access_type']
    list_filter = (AccesTypeClasseFilter,)
    
    @admin.display(description= "Opus")
    def opus(self, Inscription):
        return Inscription.opus.name

admin.site.register(models.Inscription, InscriptionAdmin)
