from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WalletConfig(AppConfig):
    name = "unpod.wallet"
    verbose_name = _("Wallet")
