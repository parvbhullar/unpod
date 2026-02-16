import re
import decimal
from urllib import parse
from unpod.common.constants import PUBLIC_EMAIL_DOMAIN
from unpod.common.string import string_to_int


class Validation:
    """
        This class validates the data object which we are receiving from the frontend
        and prepares the by replacing the null and to suitable type.
    """

    def __init__(self, required_fields, data, data_type={}):
        """
        required_fields -: These are the fields which are mandatory to be present in data.
        data -: This is the actual data which we get from the frontend
        dataTypes-: By default each and every data field will be set to string
                    but if we provide it in the dataTypes dictionary it will be replaced by that value.
        """
        self.required_fields = required_fields
        self.data = data
        self.dataType = data_type
        self.error = []

    def check_required_fields(self):
        for field in self.required_fields:
            if field not in self.data:
                self.error.append({field: "This field is mandatory."})
                return False
            if field in self.data and ((isinstance(self.data[field], str) and self.data[field] == '')):
                self.error.append({field: "This field cannot be blank."})
                return False
        return len(self.error) == 0

    def setData(self):
        for key in self.dataType:
            if key not in self.data:
                self.data[key] = self.dataType[key]
            if key in self.data and (not self.data[key]):
                self.data[key] = self.dataType[key]

    def get_data(self):
        return self.data

    def get_error(self):
        return self.error


def validate_mobile(number):
    regex = r'^\+?1?\d{9,15}$'
    return re.match(regex, number)


def validate_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.match(regex, email)


def validate_float(value):
    try:
        value = float(value)
        return value
    except:
        return False


def validate_decimal(value):
    try:
        value = decimal.Decimal(value)
        return value
    except:
        return False


def fetch_email_domain(email):
    return parse.splituser(email)[1]

def validate_email_type(email):
    domain = fetch_email_domain(email)
    return not (domain in PUBLIC_EMAIL_DOMAIN)

def get_user_id(request):
    if request.user.is_authenticated:
        return request.user.id, True
    session_user = request.data.get('session_user') or request.query_params.get('session_user')
    if session_user:
        if len(str(session_user)) > 8:
            session_user = string_to_int(str(session_user), 8)
        if type(session_user) is str:
            session_user = string_to_int(session_user, 8)
    return session_user, False