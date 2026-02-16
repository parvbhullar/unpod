from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ContactViewSet, register_user, DemoEmailViewSet

router = DefaultRouter()
router.register(r"", ContactViewSet, basename="contact")

urlpatterns = [
    *router.urls,
    # Additional URL patterns can be added here if needed
    # e.g., path('some-other-endpoint/', SomeOtherView.as_view(), name='some-other-endpoint'),
    # path('admin/contacts/export/', export_all_contacts_csv, name='admin_export_contacts_csv'),
    path(
        "demo-email/",
        DemoEmailViewSet.as_view({"get": "demo_email"}),
        name="demo_email",
    ),
    path(
        "admin/contacts/contact/<int:contact_id>/register-as-user/",
        register_user,
        name="register-as-user",
    ),
]
