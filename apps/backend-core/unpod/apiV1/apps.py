from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Apiv1Config(AppConfig):
    name = 'unpod.apiV1'
    verbose_name = _("apiV1")
