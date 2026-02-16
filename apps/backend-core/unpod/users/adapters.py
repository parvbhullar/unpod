from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin, EmailAddress
from django.conf import settings
from django.http import HttpRequest
from unpod.users.models import User, UserBasicDetail


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest):
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin: SocialLogin, form=None):
        user = super().save_user(request, sociallogin, form)
        user.email = user.email.lower()
        user.username = user.username.lower()
        user.is_social = True
        user.mode = "social"
        user.save()
        user_obj, created = UserBasicDetail.objects.get_or_create(user=user)
        return user

    def is_open_for_signup(self, request: HttpRequest, sociallogin: Any):
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def populate_user(self, request, sociallogin: SocialLogin, data):
        user = super().populate_user(request, sociallogin, data)
        user_exists = User.objects.filter(username=user.email.lower()).first()
        if user_exists:
            user = user_exists
        else:
            user.username = user.email.lower()
            user.email = user.email.lower()
        user.is_active = True
        user.is_social = True
        user.mode = "social"
        user.verify_email = True
        user.save()
        user_obj, created = UserBasicDetail.objects.get_or_create(user=user)
        return user

    def pre_social_login(self, request: HttpRequest, sociallogin: SocialLogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed
        (and before the pre_social_login signal is emitted).

        You can use this hook to intervene, e.g. abort the login by
        raising an ImmediateHttpResponse.

        Why both an adapter hook and the signal? Intervening in
        e.g. the flow from within a signal handler is bad -- multiple
        handlers may be active and are executed in undetermined order.
        """
        user = User.objects.filter(username=sociallogin.email_addresses[0]).first()
        if user:
            user.verify_email = True
            user.email = user.username
            try:
                sociallogin.connect(request, user)
            except Exception as e:
                print(f"Error connecting social login: {e}")
            return

        if sociallogin.is_existing or not sociallogin.email_addresses:
            return

        first_email = next(
            (email for email in sociallogin.email_addresses if email.verified), None
        )

        if not first_email:
            return

        try:
            existing_email = EmailAddress.objects.get(email__iexact=first_email.email)
        except EmailAddress.DoesNotExist:
            return

        sociallogin.connect(request, existing_email.user)
        user = existing_email.user
        user.is_active = True
        user.is_social = True
        user.mode = "social"
        user.verify_email = True
        user.save()
        existing_email.verified = True
        existing_email.save()
