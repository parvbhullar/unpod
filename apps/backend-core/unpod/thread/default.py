def populate_thread_roles():
    from unpod.thread.constants import DEFAULT_THREAD_ROLES
    from unpod.roles.models import Roles

    for role in DEFAULT_THREAD_ROLES:
        role_obj, created = Roles.objects.get_or_create(**role, role_type="thread", is_default=True)


def populate_post_roles():
    from unpod.thread.constants import DEFAULT_POST_ROLES
    from unpod.roles.models import Roles

    for role in DEFAULT_POST_ROLES:
        role_obj, created = Roles.objects.get_or_create(**role, role_type="post", is_default=True)

def updateCount():
    from unpod.thread.models import ThreadPost
    all_thread = ThreadPost.objects.all()   
    for thread in all_thread:
        rel_post = ThreadPost.objects.filter(parent_id=thread.id)
        sub_post_count = rel_post.filter(post_rel='seq_post').count()
        reply_count = rel_post.filter(post_rel = 'reply').count()
        if sub_post_count or reply_count:
            print(sub_post_count, reply_count)
            thread.post_count = sub_post_count
            thread.reply_count = reply_count
            thread.save()

def populatePostSlug():
    from unpod.thread.models import ThreadPost
    from unpod.thread.utils import generatePostSlug
    all_thread = ThreadPost.objects.filter(slug__isnull=True)
    print(all_thread.count())
    for thread in all_thread:
        thread.slug = generatePostSlug(thread.space, thread)
        thread.save()