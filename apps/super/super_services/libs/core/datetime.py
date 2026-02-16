# import time
from datetime import datetime
from typing import Dict

import pytz

from super_services.libs.config import settings
from super_services.libs.core.constant import DATETIME_FORMAT

# import time

tz = pytz.timezone(settings.TZ)


def get_datetime_now(utc=False):
    if utc:
        return datetime.now(pytz.utc)
    return datetime.now(tz)


def get_create_modify(utc=False) -> Dict:
    today = get_datetime_now(utc=utc)
    return {"created": today, "modified": today}


def get_modify() -> Dict:
    today = get_datetime_now()
    return {"modified": today}


def str_to_datetime(date_str, date_format=DATETIME_FORMAT):
    if isinstance(date_str, str):
        date = datetime.strptime(date_str, date_format)
    date = date.astimezone(tz)
    offset = date.utcoffset()
    date = date - offset
    return date


def remove_date_fields(data):
    for key in DATETIME_FIELDS:
        if key in data:
            data.pop(key)
    return data


def get_financial_year_from_date(dt, period=None):
    try:
        month = int(dt.split("-")[1])
        year = int(dt.split("-")[2])
        if period and period != None and period != "":
            month = int(period.split("-")[0])
            year = int(period.split("-")[1])
        ans = ""
        if month <= 3:
            ans = str(year - 1) + "-" + str(year)[2:]
        else:
            ans = str(year) + "-" + str(int(str(year)[2:]) + 1)
        return ans
    except BaseException:
        return ""


def get_datetime_now_str(utc=False, DATETIME_FORMAT=DATETIME_FORMAT):
    now_time = get_datetime_now(utc=utc)
    return now_time.strftime(DATETIME_FORMAT)


def convert_time_into_unit(
    days=0, minutes=0, hours=0, weeks=0, months=0, years=0, unit="seconds"
):
    """
    month -> will be of 30 days
    year -> will be of 365 days
    unit(convert to) = microseconds / milliseconds / seconds / minutes or hours
    """
    day_seconds = 24 * 60 * 60

    total_seconds = (
        (days + (weeks * 7) + (months * 30) + (years * 365)) * day_seconds
        + (hours * 60 * 60)
        + (minutes * 60)
    )

    if unit == "seconds":
        return total_seconds
    elif unit == "minutes":
        return total_seconds / 60
    elif unit == "hours":
        return total_seconds / 3600
    elif unit == "microseconds":
        return total_seconds * 1000000
    elif unit == "milliseconds":
        return total_seconds * 1000
