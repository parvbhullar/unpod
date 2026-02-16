from django.db.models import Q, Model
from .string import generate_code


def create_search_query(model: Model, search_keyword, key_list=[], queryset=None):
    query = Q()
    for key in key_list:
        if hasattr(model, key):
            query.add(Q(**{f"{key}__icontains": search_keyword}), Q.OR)
    if queryset:
        queryset = queryset.filter(query)
    else:
        queryset = model.objects.filter(query)
    return queryset


def get_model_unique_code(model, field, N=16):
    token = generate_code(N)
    query = Q()
    query.add(Q(**{field: token}), Q.AND)
    while model.objects.filter(query).exists():
        token = generate_code(N)
    return token


def generateSpaceSlug(space):
    from django.utils.text import slugify

    space_slug = f"{space.name}-{space.token[:4]}{space.token[-4:]}"
    space_slug = slugify(space_slug)
    return space_slug


def unique_slugify(instance, value, slug_field_name="slug"):
    from django.utils.text import slugify

    """
    Generate a unique slug for a model instance.
    """
    slug = slugify(value)
    ModelClass = instance.__class__

    # Start with the original slug
    unique_slug = slug
    counter = 1

    # Check if slug already exists in DB
    while (
        ModelClass.objects.filter(**{slug_field_name: unique_slug})
        .exclude(pk=instance.pk)
        .exists()
    ):
        unique_slug = f"{slug}-{counter}"
        counter += 1

    return unique_slug


def generate_new_number(last_number: str = "", prefix: str = "INV-", digits=5) -> str:
    if last_number is not None and len(last_number) > 0:
        if prefix in last_number:
            # Remove prefix if exists
            last_number = int(last_number.replace(prefix, ""))
        else:
            last_number = int(last_number)

        new_number = last_number + 1
    else:
        new_number = 1

    new_number_str = str(new_number).zfill(digits)
    return f"{prefix}{new_number_str}"
