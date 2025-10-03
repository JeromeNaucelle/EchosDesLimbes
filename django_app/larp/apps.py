from django.apps import AppConfig


class LarpConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'larp'

    def ready(self):
        from . import signals
        return super().ready()
