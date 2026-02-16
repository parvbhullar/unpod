from unpod.roles.constants import ROLE_BASED_OPERATION
from unpod.roles.models import AccountTags
from django.utils.text import slugify


def getTag(slug):
    if slug == None:
        return None
    slug = slugify(slug)
    return AccountTags.objects.filter(slug=slug).first()


def getRoleBasedOperation(role_code, role_type):
    role_type_operation = ROLE_BASED_OPERATION.get(role_type, {})
    return role_type_operation.get(role_code, role_type_operation.get("viewer")) or []
