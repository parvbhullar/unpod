from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Apiv2PlatformConfig(AppConfig):
    name = 'unpod.apiV2Platform'
    verbose_name = _("API V2 Platform")
    default_auto_field = 'django.db.models.BigAutoField'