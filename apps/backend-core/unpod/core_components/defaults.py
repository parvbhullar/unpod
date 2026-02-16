def populate_profiles():
    from unpod.core_components.constants import PROFILEROLES
    from unpod.core_components.models import ProfileRoles

    for role in PROFILEROLES:
        role_name = role.pop("role_name")
        role_code = role.pop("role_code")
        ProfileRoles.objects.get_or_create(
            role_name=role_name, role_code=role_code, defaults=role
        )
