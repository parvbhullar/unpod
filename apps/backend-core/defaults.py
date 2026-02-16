from unpod.roles.defaults import populate_tags
from unpod.core_components.defaults import populate_profiles
from unpod.space.default import populate_space_roles
from unpod.thread.default import populate_thread_roles, populate_post_roles


def populate_data():
    populate_tags()
    populate_profiles()
    populate_space_roles()
    populate_post_roles()
    populate_thread_roles()
