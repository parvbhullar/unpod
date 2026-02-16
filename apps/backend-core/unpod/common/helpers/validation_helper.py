from django.core.exceptions import ValidationError

from unpod.common.constants import DOMAIN_REGEX


def validate_domain(value):
    if not DOMAIN_REGEX.match(value):
        raise ValidationError("Enter a valid domain name")
