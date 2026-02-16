class Entity:
    def __init__(self, id, type, name, privacy, relationship, parent_id):
        self.id = id
        self.type = type
        self.name = name
        self.privacy = privacy
        self.relationship = relationship
        self.parent_id = parent_id

    def __str__(self):
        return f"Id={self.id}, Name={self.name}, Type={self.type}, Privacy={self.privacy}, Relationship={self.relationship}, ParentId={self.parent_id}"

    def to_dict(self):
        return self.__dict__


class UserPermission:
    def __init__(self, id, user, role, entity_id, entity_type):
        self.id = id
        self.user = user
        self.role = role
        self.entity_id = entity_id
        self.entity_type = entity_type

    def __str__(self):
        return f"Id={self.id}, Type={self.entity_type}, Role={self.role} - User={self.user}"

    def to_dict(self):
        return self.__dict__


class PermissionMatrix:
    def __init__(self, entity_level, parent_role, role, entity_privacy, allowed_permissions):
        self.entity_level = entity_level
        self.parent_role = parent_role
        self.role = role
        self.entity_privacy = entity_privacy
        self.allowed_permissions = allowed_permissions

    def __str__(self):
        return f"PermissionMatrix(EntityLevel={self.entity_level}, ParentRole={self.parent_role}, Role={self.role}, EntityPrivacy={self.entity_privacy}, AllowedPermissions={self.allowed_permissions})"

    def to_dict(self):
        return self.__dict__


class PermissionManager:
    def __init__(self, entities, user_permissions):
        self.entities = entities
        self.user_permissions = user_permissions
        self.permission_matrix = load_permission_matrix()

    # Assuming the provided data is stored in variables:
    # user_permissions, entities, permission_matrix

    def find_user_permissions(self, user_id, entity_id):
        """Return the user's role on the given entity, or None if not found."""
        for permission in self.user_permissions:
            if permission['user'] == user_id and permission['entity_id'] == entity_id:
                return permission['role']
        return None

    def find_entity(self, entity_id):
        """Return the entity with the given id, or None if not found."""
        for entity in self.entities:
            if entity['id'] == entity_id:
                return entity
        return None

    def find_permissions(self, role, entity_privacy):
        """Return the allowed permissions for the given role and entity privacy, or None if not found."""
        # filter permission matrix by role and entity privacy
        for permission in self.permission_matrix:
            print(permission['role'], role, permission['entity_privacy'], entity_privacy)
            if permission['role'].lower() == role and permission['entity_privacy'] == entity_privacy:
                return permission['allowed_permissions']
        return []

    def filter_permissions(self, role, entity_privacy, entity_level):
        """Return the allowed permissions for the given role and entity privacy, or None if not found."""

        # Convert entity_type to entity_level based on given assumption

        # Filter the permission matrix
        filtered_permissions = [
            permission.get('allowed_permissions', []) for permission in self.permission_matrix
            if (
                permission.get('role', '') == str(role) and
                permission.get('entity_privacy', '') == entity_privacy
            )
        ]

        return filtered_permissions

    def get_permissions(self, user_id, entity_id):
        # Find the user's role for the given entity
        allowed_permissions = []
        for entity in self.entities:
            role = self.find_user_permissions(user_id, entity['id'])
            print(entity['privacy'], role, user_id)
            entity['relationship'] = 'parent' if entity['id'] != entity_id else 'entity'
            allowed_permissions = self.filter_permissions(role, entity['privacy'], entity['relationship'])
            # if role is not None:
            entity['role'] = role

            entity['allowed_permissions'] = allowed_permissions

        # role = self.find_user_permissions(user_id, entity.id)

        # # If the user has a role on the entity, find the entity's details and the allowed permissions
        # if role is not None:
        #     entity = self.find_entity(entity.id)
        #     if entity is not None:
        #         allowed_permissions = self.find_permissions(role, entity['privacy'])
        #         print(allowed_permissions)
        #     else:
        #         print("Entity not found")
        # else:
        #     print("User does not have a role on the specified entity")

        return self.entities


# Create entities
entities = [
    Entity("H1", "Organization", "MI", "Shared", "entity", ""),
    Entity("S1", "Space", "DevOps", "Shared", "child", "H1"),
    Entity("T1", "Thread", "KT Videos", "Shared", "child", "S1"),
    Entity("P1", "Post", "ACM", "Shared", "child", "T1")
]

# Create user permissions
user_permissions = [
    UserPermission(1, "Parvinder", "owner", "H1", "Organization"),
    UserPermission(2, "Anuj", "editor", "H1", "Organization"),
    UserPermission(3, "Yogi", "viewer", "H1", "Organization"),
    UserPermission(4, "Anuj", "owner", "S1", "Space"),
    UserPermission(5, "Yogi", "viewer", "S1", "Space"),
    UserPermission(6, "Parvinder", "editor", "S1", "Space"),
]


def load_permission_matrix():
    global permission_matrix, data, entity_privacy
    # Create permission matrix
    permission_matrix_data = [
        ("entity", "None", "owner", "private,shared,public,link",
         ["add", "edit", "delete", "share_entity", "share_permission", "view_list", "view_content", "comment",
          "use_superpilot", "transfer_ownership"]),
        ("child", "owner", "None", "private", ["transfer_ownership", "delete"]),
        ("child", "owner", "viewer", "shared,public,link",
         ["add", "edit", "share_entity", "share_permission", "view_list", "view_content", "comment", "use_superpilot"]),
        ("child", "owner", "editor", "shared,public,link",
         ["add", "edit", "share_entity", "share_permission", "view_list", "view_content", "comment", "use_superpilot"]),
        ("entity", "None", "editor", "shared,public,link",
         ["add", "edit", "share_entity", "share_permission", "view_list", "view_content", "comment", "use_superpilot"]),
        ("child", "editor", "None", "private", []),
        ("child", "editor", "viewer", "shared,public,link",
         ["add", "share_entity", "share_permission", "view_list", "view_content", "comment", "use_superpilot"]),
        ("child", "editor", "editor", "shared,public,link",
         ["add", "edit", "delete", "share_entity", "share_permission", "view_list", "view_content", "comment",
          "use_superpilot"]),
        ("entity", "None", "viewer", "shared,public,link",
         ["share_entity", "share_permission", "view_list", "view_content", "comment", "use_superpilot"]),
        ("child", "viewer", "None", "private,shared", []),
        ("child", "viewer", "viewer", "shared,public,link",
         ["share_entity", "share_permission", "view_list", "view_content", "comment", "use_superpilot"]),
        ("child", "viewer", "editor", "shared,public,link",
         ["add", "edit", "delete", "share_entity", "share_permission", "view_list", "view_content", "comment",
          "use_superpilot"]),
        ("entity", "None", "None", "public,link", ["view_list", "view_content", "comment"])
    ]
    # Create a list of PermissionMatrix objects from the data above,
    # creating separate entries for each 'EntityPrivacy' value.
    permission_matrix = []
    for data in permission_matrix_data:
        load_permission_matrix = data[3].split(',')
        for entity_privacy in load_permission_matrix:
            permission_matrix.append(PermissionMatrix(data[0], data[1], data[2], entity_privacy, data[4]).to_dict())
            # print((data[0], data[1], data[2], entity_privacy, data[4]))
    return permission_matrix


# permission_matrix = load_permission_matrix()
# # print(permission_matrix)
#
# # Create a PermissionManager object
# permission_manager = PermissionManager(entities, user_permissions, permission_matrix)
#
# # Get permissions for a user
# permissions = permission_manager.get_permissions("Parvinder", "S1")
# print(permissions)
# permissions = permission_manager.get_permissions("Yogi", "H1")
# print(permissions)
