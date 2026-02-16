from unpod.space.constants import SPACE_ALL_TOKEN


def populate_space_roles():
    from unpod.space.constants import DEFAULT_SPACE_ROLES
    from unpod.roles.models import Roles

    for role in DEFAULT_SPACE_ROLES:
        role_obj, created = Roles.objects.get_or_create(**role, role_type="space", is_default=True)
    
    for role in DEFAULT_SPACE_ROLES:
        role_obj, created = Roles.objects.get_or_create(**role, role_type="organization", is_default=True)


def getAllSpaceObject():
    space = {
        "name": "All",
        "token": SPACE_ALL_TOKEN
    }
    return space

def updateOrgMember():
    from unpod.users.models import User
    from unpod.space.models import OrganizationMemberRoles, SpaceMemberRoles
    from unpod.roles.models import Roles
    
    all_users = User.objects.all()
    for user in all_users:
        org_dict = {}
        space_org_id = SpaceMemberRoles.objects.filter(user=user).values_list('space__space_organization_id', flat=True).distinct()
        for org_id in space_org_id:
            space_obj = SpaceMemberRoles.objects.filter(space__space_organization_id=org_id, user=user).order_by('space_id').first()
            if space_obj.role.role_code == 'owner':
                role, created = Roles.objects.get_or_create(role_type="organization", is_default=True, role_code ='owner')
                org_member_role, created = OrganizationMemberRoles.objects.get_or_create(organization_id=org_id, user=user, role=role, defaults={'grant_by': user.id})
            else:
                role, created = Roles.objects.get_or_create(role_type="organization", is_default=True, role_code ='viewer')
                org_member_role, created = OrganizationMemberRoles.objects.get_or_create(organization_id=org_id, user=user, role=role, defaults={'grant_by': user.id})

def updateOrgActive():
    from unpod.users.models import User
    from unpod.space.models import OrganizationMemberRoles
    
    all_users = User.objects.all()
    for user in all_users:
        org = OrganizationMemberRoles.objects.filter(user=user).first()
        if hasattr(user, 'userbasicdetail_user') and org:
            print(user.userbasicdetail_user)
            user.userbasicdetail_user.active_organization = org.organization
            user.userbasicdetail_user.save()