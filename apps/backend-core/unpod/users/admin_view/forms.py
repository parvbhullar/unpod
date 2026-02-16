from django import forms

class OTPLoginForm(forms.Form):
	username = forms.CharField(label='Username')
	password = forms.CharField(label='Password')
	otp = forms.CharField(label="OTP")


class LoginForm(forms.Form):
	username = forms.CharField(label='Username')
	password = forms.CharField(label='Password')
