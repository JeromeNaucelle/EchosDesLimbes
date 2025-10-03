from django.contrib import admin
from . import models


# Register your models here.
admin.site.register(models.Larp)
admin.site.register(models.Faction)
admin.site.register(models.Ticket)
admin.site.register(models.Inscription)
admin.site.register(models.Trigger)
admin.site.register(models.Profile)

class OpusAdmin(admin.ModelAdmin):
    exclude=('pj_form', 'pnj_form', )

admin.site.register(models.Opus, OpusAdmin)