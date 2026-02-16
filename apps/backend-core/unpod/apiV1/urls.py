from django.urls import include, path

# fmt: off
urlpatterns = [
    path('', include('unpod.users.urls'), name="users_v1"),
    path('', include('unpod.core_components.urls'), name="core_components_v1"),
    path('organization/', include('unpod.space.org_urls'), name="space_organization_v1"),
    path('spaces/', include('unpod.space.urls'), name="space_v1"),
    path('threads/', include('unpod.thread.urls'), name="thread_v1"),
    path('roles/', include('unpod.roles.urls'), name="roles_v1"),
    path('notifications/', include('unpod.notification.urls'), name="notification_v1"),
    path('subscriptions/', include('unpod.subscription.urls'), name="subscription_v1"),
    path('knowledge_base/', include('unpod.knowledge_base.urls'), name="knowledge_base_v1"),
    path('wallet/', include('unpod.wallet.urls'), name="wallet_v1"),
    path('channels/', include('unpod.channels.urls')),
    path('tasks/', include('unpod.core_components.tasks.urls')),
    path('telephony/', include('unpod.telephony.urls'), name="sip_v1"),
    path('documents/', include('unpod.documents.urls'), name="documents"),
    path('contacts/', include('unpod.contacts.urls'), name="contacts"),
    path('metrics/', include('unpod.metrics.urls'), name="metrics"),
    path('dynamic-forms/', include('unpod.dynamic_forms.urls'), name="dynamic_forms_base"),
]
