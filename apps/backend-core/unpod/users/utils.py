from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils import timezone

from unpod.common.helpers.service_helper import send_email
from unpod.common.otp import send_otp, send_verify_email_otp
from unpod.common.redis import get_status
from unpod.common.utils import get_global_configs, get_app_info
from unpod.common.validation import fetch_email_domain, validate_email_type
from unpod.space.models import OrganizationInvite, SpaceInvite, SpaceOrganization
from unpod.users.models import Roles, UserBasicDetail, UserRoles
from unpod.common.jwt import jwt_encode_handler, jwt_payload_handler
from unpod.common.storage_backends import imagekitBackend

User = get_user_model()


def getUser(user_id):
    return User.objects.filter(id=user_id).first()


def check_user(email, number, is_number):
    check_user_data = dict()
    if is_number:
        check_user_data.update({"phone_number": number})
    else:
        check_user_data.update({"email": email})
    return User.objects.filter(**check_user_data).first()


def getAllUserByEmail(user_list) -> dict:
    user_dict = {}
    user_obj = User.objects.filter(email__in=user_list)
    for user in user_obj:
        user_dict[user.email] = user
    return user_dict


def get_name(first_name, last_name):
    name = ""
    if first_name and first_name != "":
        name = name + first_name + " "
    if last_name and last_name != "":
        name = name + last_name
    return name


def send_mail_contact_as_user(user, password, product_id=None):
    app = get_app_info(product_id)
    APP_NAME = app.get("APP_NAME")
    APP_URL = app.get("APP_URL")

    subject = f"Welcome to {APP_NAME}! Your Account Has Been Created"
    email_from = settings.EMAIL_FROM_ADDRESS
    recipient_list = [
        user.email,
    ]
    context = {
        "user": user,
        "password": password,
        "signin_url": f"{APP_URL}/auth/signin",
        **app,
    }

    html_content = render_to_string("emails/contact_welcome_email.html", context)
    send_email(
        subject,
        email_from,
        recipient_list,
        mail_body=html_content,
        mail_type="html",
    )


def send_mail_user_register(user, is_contact=False, product_id=None):
    app = get_app_info(product_id)

    subject = f"New User Registration: {user.get_full_name() or user.email}"
    if is_contact:
        subject = (
            f"New User Registration from Contact: {user.get_full_name() or user.email}"
        )

    email_from = settings.EMAIL_FROM_ADDRESS
    email_recipient = get_global_configs("email-recipient")
    recipient_list = email_recipient.get("new_user_register", [])

    context = {
        "user": user,
        "full_name": user.get_full_name() or user.email,
        "created_at": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_url": f"{settings.BASE_URL}/{settings.ADMIN_URL}/users/user/{user.id}/change/",
        **app,
    }

    html_content = render_to_string("emails/new_user_register.html", context)
    send_email(
        subject,
        email_from,
        recipient_list,
        mail_body=html_content,
        mail_type="html",
    )


def register_contact_as_user(contact, password, product_id=None):
    user = check_user(contact.email, None, False)

    if not user:
        # If user does not exist, create a new user
        user = User.objects.create(
            username=contact.email,
            mode="Email",
            email=contact.email,
            phone_number=contact.phone,
            is_active=True,
            verify_email=True,
            verify_mob=True,
        )
        user.set_password(password)
        user.save()
        user.update_name(contact.name)
        user_role, created = Roles.objects.get_or_create(name="User")
        UserRoles.objects.update_or_create(user=user, defaults={"role": user_role})
        UserBasicDetail.objects.get_or_create(user=user)

        # Send welcome email to user
        send_mail_contact_as_user(user, password, product_id=product_id)

        # Send mail to admin about new user registration
        send_mail_user_register(user, is_contact=True, product_id=product_id)

        return user
    else:
        # If user exists, update the existing user
        message = "User Already Exists for this Email/Number"
        raise ValueError(message)


def otp_generation(email, password, extra_data):
    error = False
    if email:
        is_email = True if email else False
        is_number = False
        number = None

        mode, username = ("Email", email)
        user = check_user(email, None, False)
        if not user or (user and not user.verify_email):
            if not user:
                user = User.objects.create(
                    username=username,
                    mode=mode,
                    email=email if is_email else None,
                    phone_number=number,
                    is_active=False,
                )
            user.set_password(password)
            user.save()
            user_role, created = Roles.objects.get_or_create(name="User")
            UserRoles.objects.update_or_create(user=user, defaults={"role": user_role})
            postUserSignUp(extra_data, user)
            otp_check, time_left, otp = get_status(
                username, str(user.id), prefix="signup"
            )
            if otp_check and is_email:
                # send_otp(email, otp, is_number=False, is_email=True)
                # send_otp_link(email, otp)
                send_verify_email_otp(email, otp)
                message = "An OTP has been sent to your email address"
            elif otp_check and is_number:
                send_otp(number, otp, is_number=True, is_email=False)
                message = "An OTP has been sent to your phone number"
            else:
                message = "Wait for " + str(time_left) + " second to send again"
                error = True
        else:
            message = "User Already Exists for this Email/Number"
            error = True
    else:
        message = "Phone Number or Email can not be empty"
        error = True
    return message, error


def send_resend_otp(email):
    error = False
    if email:
        is_email = True if email else False
        is_number = False
        number = None

        mode, username = ("Email", email)
        user = check_user(email, None, False)
        if user and user.verify_email:
            message = "Email Already Verified"
            error = True
            return message, error
        if user:
            otp_check, time_left, otp = get_status(
                username, str(user.id), prefix="signup"
            )
            if otp_check and is_email:
                # send_otp(email, otp, is_number=False, is_email=True)
                # message = "OTP sent successfully"
                # send_otp_link(email, otp)
                send_verify_email_otp(email, otp)

                message = "An OTP has been resent to your email address"
            elif otp_check and is_number:
                send_otp(number, otp, is_number=True, is_email=False)
                message = "An OTP has been resent to your phone number"
            else:
                message = "Wait for " + str(time_left) + " second to send again"
                error = True
        else:
            message = "Please SignUp First, No User Exists with this Email"
            error = True
    else:
        message = "Phone Number or Email can not be empty"
        error = True
    return message, error


def checkInvited(email):
    check_dt = timezone.now() - timezone.timedelta(days=1)
    check_space = SpaceInvite.objects.filter(
        user_email=email, invite_verified=True, invite_verify_dt__gt=check_dt
    ).exists()
    check_org = OrganizationInvite.objects.filter(
        user_email=email, invite_verified=True, invite_verify_dt__gt=check_dt
    ).exists()
    if check_space or check_org:
        user = check_user(email, None, False)
        if user is None or not user.verify_email:
            if check_org:
                return "organization"
            if check_space:
                return "space"
        return None
    return None


def processInvitedUser(email, password, request_data, invite_type):
    from unpod.users.serializers import UserSerializer
    from unpod.space.serializers import SpaceListSerializers

    extra_data = {}
    user, created = User.objects.update_or_create(
        email=email,
        defaults={
            "mode": "Email",
            "username": email,
            "phone_number": None,
            "is_active": True,
            "verify_email": True,
        },
    )
    user.set_password(password)
    user.save()
    user_role, created = Roles.objects.get_or_create(name="User")
    UserRoles.objects.update_or_create(user=user, defaults={"role": user_role})
    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)
    postUserSignUp(request_data, user)
    extra_data["user"] = UserSerializer(user).data
    invite_data = []
    if invite_type == "space":
        check_dt = timezone.now() - timezone.timedelta(days=1)
        check_spc = (
            SpaceInvite.objects.filter(
                user_email=email, invite_verified=True, invite_verify_dt__gt=check_dt
            )
            .select_related("space")
            .first()
        )
        if check_spc:
            space = SpaceListSerializers(check_spc.space).data
            space["invite_token"] = check_spc.invite_token
            extra_data.update({"invite_type": invite_type, "space": space})
    else:
        check_dt = timezone.now() - timezone.timedelta(days=1)
        org_invite = OrganizationInvite.objects.filter(
            user_email=email, invite_verified=True, invite_verify_dt__gt=check_dt
        ).first()
        if org_invite:
            domain, org = org_invite.organization.domain_handle, org_invite.organization
            extra_data.update(
                {
                    "invite_type": invite_type,
                    "domain": domain,
                    "organization": org.to_json(
                        [
                            "name",
                            "token",
                            "domain",
                            "domain_handle",
                            "is_private_domain",
                        ]
                    ),
                }
            )
    return {
        "success": "Your Registration is Successful",
        "token": token,
        "verification_done": True,
        "invitation_list": invite_data,
        **extra_data,
    }


def postUserSignUp(extra_data, user):
    user = user.update_name(extra_data.get("name"))
    user_obj, created = UserBasicDetail.objects.get_or_create(user=user)
    user_obj.updateModel(extra_data)
    return user


def checkUserOragaization(user):
    domain = fetch_email_domain(user.email)
    if validate_email_type(user.email):
        fields = [
            "name",
            "token",
            "domain",
            "account_type",
            "logo",
            "domain_handle",
            "is_private_domain",
        ]
        org = (
            SpaceOrganization.objects.filter(
                domain_handle=domain, is_private_domain=True
            )
            .values(*fields)
            .first()
        )
        if org:
            org["logo"] = imagekitBackend.generateURL(org["logo"])
        return domain, org
    return domain, None


def updateActiveOrg(user, org):
    user.userbasicdetail_user.active_organization = org
    user.userbasicdetail_user.save()
    return user.userbasicdetail_user
