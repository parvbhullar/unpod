from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from unpod.common.mixin import ChoiceEnum, CreatedUpdatedMixin


class RoleTypeEnum(ChoiceEnum):
    space = 'Space'
    thread = 'Thread'
    post = 'Post'
    organization = 'Organization'


class Roles(CreatedUpdatedMixin):
    role_name = models.CharField(max_length=30, db_index=True)
    role_code = models.CharField(max_length=30, db_index=True)
    role_type = models.CharField(max_length=30, db_index=True, choices=RoleTypeEnum.choices())
    is_default = models.BooleanField(default=True, db_index=True)
    role_metadata = models.JSONField(default=dict, null=True, blank=True, encoder=DjangoJSONEncoder)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.role_name} - {self.role_type}"


class TagsType(ChoiceEnum):
    roles = 'Roles'
    requirement = 'Requirement'
    industries = 'Industries'
    countries = 'Countries'
    languages = 'Languages'
    skills = 'Skills'
    frameworks = 'Frameworks'
    tools = 'Tools'
    database = 'Database'
    payments = 'Payments'
    engineering = 'Engineering'


class AccountTags(CreatedUpdatedMixin):
    name = models.CharField(max_length=30, db_index=True)
    icon = models.CharField(max_length=199, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    slug = models.CharField(max_length=30, db_index=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='%(class)s_parent')
    tag_type = models.CharField(max_length=30, db_index=True, choices=TagsType.choices())
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name} - {self.tag_type}"
