from django.apps import AppConfig
from django.conf.global_settings import DEFAULT_AUTO_FIELD


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.signals  #this is the start of the signal (post_save)
                            #which created the wallet with each new user object

