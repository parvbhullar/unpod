from django.conf import settings
from django.utils import timezone
import pytz

IST_TZ = pytz.timezone("Asia/Kolkata")


def get_datetime_now(IST=False):
    if IST:
        return timezone.datetime.now(tz=IST_TZ)
    return timezone.datetime.now(tz=timezone.get_current_timezone())


def datetime_from_timestamp(timestamp, IST=False):
    if len(str(timestamp)) > 10:
        timestamp = int(str(timestamp)[:10])
    dt = timezone.datetime.fromtimestamp(timestamp, tz=timezone.get_current_timezone())
    if IST:
        return dt.astimezone(IST_TZ)
    return dt


def date_to_datetime(date):
    return timezone.datetime.combine(date, timezone.datetime.min.time())


def get_days_in_month(year, month):
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    first_day_next_month = timezone.datetime(next_year, next_month, 1)
    last_day_current_month = first_day_next_month - timezone.timedelta(days=1)
    return last_day_current_month.day


def get_formated_date(dt, fmt: str = settings.DATETIME_FORMAT) -> str:
    return dt.strftime(fmt)
