from django.urls import path

from unpod.roles.views import RoleViewSet, TagsViewSet

app_name = "roles_v1"

urlpatterns = [
    path('<str:role_type>/', RoleViewSet.as_view({"get": "list"}), name='role-list'),
    path('permission-allowed/<str:role_type>/', RoleViewSet.as_view({"get": "list_permission"}), name='role-allowed'),
    path('tags/<str:tag_type>/', TagsViewSet.as_view({"get": "list"}), name='role-list'),
]
