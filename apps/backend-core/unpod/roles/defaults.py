def populate_tags():
    from unpod.roles.constants import TAGS_DATA
    from unpod.roles.models import AccountTags
    from django.utils.text import slugify

    for tagtype, tags in TAGS_DATA.items():
        for tag in tags:
            name = tag.pop('name')
            slug = slugify(name)
            default = {'slug': slug, **tag}
            AccountTags.objects.get_or_create(tag_type=tagtype, name=name, defaults=default)
