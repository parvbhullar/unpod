import re

PUBLIC_EMAIL_DOMAIN = [
    "gmail.com",
    "yahoo.co",
    "yahoo.co.in",
    "outlook.com",
    "hotmail.com",
    "microsoft.com",
    "yopmail.com",
    "icloud.com",
    "protonmail.com",
    "gmx.com",
    "mail.com",
    "fastmail.com",
    "zoho.com",
    "zohomail.in",
]

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

DOMAIN_REGEX = re.compile(r"^(?!-)([A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$")
