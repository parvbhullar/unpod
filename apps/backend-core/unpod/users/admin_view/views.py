import os
from django.views import View
from unpod.common.otp import send_admin_otp
from unpod.common.redis import delete_key, get_otp, get_status
from unpod.users.admin_view.forms import LoginForm, OTPLoginForm
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.conf import settings

# fmt:off
class AdminLogin(View):

    def get(self, request):
        form = LoginForm()
        config_file = os.environ.get('DJANGO_SETTINGS_MODULE')
        button_value = 'Log in' if 'local' in config_file.lower() else 'Send OTP'
        return render(request, settings.ADMIN_LOGIN_TEMPLATE, {"form": form, "button_value": button_value})

    def post(self, request):
        _form = LoginForm()
        if request.POST.get('otp'):
            _form = OTPLoginForm(request.POST)
            if _form.is_valid():
                otp_from_redis = get_otp(_form.data["username"], _form.data["username"], prefix='admin-login')
                if not otp_from_redis:
                    return render(request, settings.ADMIN_LOGIN_TEMPLATE, {"form": _form, "button_value": 'Send OTP', "error": "Invalid OTP."})
                user = authenticate(username=_form.data["username"],
                                    password=_form.data["password"])
                if user:
                    if otp_from_redis == _form.data["otp"]:
                        login(request, user)
                        delete_key(_form.data["username"],_form.data["username"], prefix='admin-login')
                        return redirect(f'/{settings.ADMIN_URL}')
                    else:
                        return render(request, settings.ADMIN_LOGIN_TEMPLATE, {"form": _form, "button_value": 'Send OTP', "error": "Invalid OTP."})
                else:
                    return render(request, settings.ADMIN_LOGIN_TEMPLATE, {"form": _form, "button_value": 'Send OTP', "error": "Username or password doesn't match."})

        else:
            _form = LoginForm(data=request.POST)
            if _form.is_valid():
                config_file = os.environ.get('DJANGO_SETTINGS_MODULE')
                button_value = 'Log in' if 'local' in config_file.lower() else 'Send OTP'
                user = authenticate(username=_form.data["username"],
                                    password=_form.data["password"])
                if user is not None:
                    if button_value == 'Log in':
                        login(request, user)
                        return redirect(f'/{settings.ADMIN_URL}')
                    email = user.email
                    if not email or email == '':
                        return render(request,settings.ADMIN_LOGIN_TEMPLATE, {"form": _form, "button_value": button_value, "error": "Email Address Not Updated, Please update the valid email address first."})
                    otp_check, time_left, otp = get_status(_form.data["username"], _form.data["username"], prefix='admin-login')
                    form = OTPLoginForm(data=request.POST)
                    if otp_check:
                        send_admin_otp(user.email, otp)
                        return render(request, settings.ADMIN_LOGIN_TEMPLATE, {"form": form, "button_value": button_value})
                    else:
                        return render(request,settings.ADMIN_LOGIN_TEMPLATE, {"form": form, "button_value": button_value, "error": f"OTP Limit Exceed, You can try after {time_left} seconds"})
                else:
                    return render(request,settings.ADMIN_LOGIN_TEMPLATE, {"form": _form, "button_value": button_value, "error": "Username or password doesn't match."})
        return render(request, settings.ADMIN_LOGIN_TEMPLATE, {"form": _form})
