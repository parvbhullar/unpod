from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.utils.crypto import get_random_string
from rest_framework import viewsets, status, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from unpod.common.renderers import UnpodJSONRenderer
from .models import Contact
from .serializers import ContactSerializer
from .utils import send_demo_email
from ..users.models import User
from ..users.utils import register_contact_as_user


class ContactViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    authentication_classes = []
    permission_classes = []
    renderer_classes = [UnpodJSONRenderer]

    def create(self, request, *args, **kwargs):
        product_id = request.headers.get("Product-Id")
        data = request.data.copy()
        data["product_id"] = product_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        return Response(
            {
                "data": serializer.data,
                "message": "Thanks, We will connect with you soon.",
            },
            status=status.HTTP_201_CREATED,
        )


class DemoEmailViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    renderer_classes = [UnpodJSONRenderer]

    def demo_email(self, request, *args, **kwargs):
        print("Demo email function called", request.user)
        if request.user and request.user.is_authenticated:
            result = send_demo_email()

        else:
            result = "Authentication required to send demo email."

        return Response(
            {"message": result, "data": {"user": ""}}, status=status.HTTP_200_OK
        )


@staff_member_required
def register_user(request, contact_id):
    try:
        contact = Contact.objects.get(id=contact_id)
        random_password = get_random_string(length=12)
        password = f"UP{contact_id}@{random_password}"  # format the password as needed
        user = register_contact_as_user(
            contact, password, product_id=contact.product_id
        )  # Assuming you have a password or some logic to set it
        contact.registered_as_user = True  # Update the contact status if needed
        contact.user = user  # Link the created user to the contact
        contact.status = "Done"  # Ensure the contact is active
        contact.save()

        messages.success(
            request, f"Contact {contact.name} is registered as a user successfully."
        )
    except Contact.DoesNotExist:
        messages.error(request, f"Contact with ID {contact_id} does not exist.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
