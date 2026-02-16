"""
Timezone utilities for business hours validation in outbound calling.

This module provides functions to:
- Extract country codes from phone numbers
- Map phone numbers to their respective timezones
- Validate if current time is within business hours (9 AM - 8 PM)
- Calculate next business hour for scheduling
"""

import os
import re
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional, Tuple

import pytz
from super.core.logging.logging import print_log
from pydantic import BaseModel, ValidationError, field_validator
import phonenumbers

# Country code to timezone mapping
# Expanded coverage: EU (15+ countries), Australia, New Zealand, and Middle East hubs.
COUNTRY_TIMEZONE_MAP = {
    "+91": "Asia/Kolkata",         # India
    "+966": "Asia/Riyadh",         # Saudi Arabia
    "+971": "Asia/Dubai",          # United Arab Emirates
    "+973": "Asia/Bahrain",        # Bahrain
    "+974": "Asia/Qatar",          # Qatar
    "+968": "Asia/Muscat",         # Oman
    "+965": "Asia/Kuwait",         # Kuwait
    "+962": "Asia/Amman",          # Jordan
    "+90": "Europe/Istanbul",      # Turkey (cross-region, aligns with EU outreach)
    "+44": "Europe/London",        # United Kingdom
    "+49": "Europe/Berlin",        # Germany
    "+33": "Europe/Paris",         # France
    "+39": "Europe/Rome",          # Italy
    "+34": "Europe/Madrid",        # Spain
    "+31": "Europe/Amsterdam",     # Netherlands
    "+32": "Europe/Brussels",      # Belgium
    "+41": "Europe/Zurich",        # Switzerland
    "+46": "Europe/Stockholm",     # Sweden
    "+47": "Europe/Oslo",          # Norway
    "+45": "Europe/Copenhagen",    # Denmark
    "+358": "Europe/Helsinki",     # Finland
    "+351": "Europe/Lisbon",       # Portugal
    "+48": "Europe/Warsaw",        # Poland
    "+43": "Europe/Vienna",        # Austria
    "+30": "Europe/Athens",        # Greece
    "+420": "Europe/Prague",       # Czech Republic
    "+36": "Europe/Budapest",      # Hungary
    "+353": "Europe/Dublin",       # Ireland
    "+61": "Australia/Sydney",     # Australia
    "+64": "Pacific/Auckland",     # New Zealand
    "+1": "America/New_York",      # United States / Canada (defaulting to Eastern Time)
}


class PhoneNumberModel(BaseModel):
    """Pydantic model for phone number validation and formatting."""
    number: str

    @field_validator('number')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """
        Validate and format phone number to E164 format.

        Args:
            v: Phone number string to validate

        Returns:
            Phone number in E164 format (e.g., +919876543210)

        Raises:
            ValueError: If phone number is invalid
        """
        if not v:
            raise ValueError("Phone number cannot be empty")

        # Get default country code from environment (ISO code, e.g., "IN" for India, "US" for USA)
        # Convert +91 to IN, +1 to US, etc.
        default_country_code_with_plus = os.getenv("DEFAULT_COUNTRY_CODE", "+91")
        country_code_map = {
            "+91": "IN",
            "+1": "US",
            "+44": "GB",
            "+86": "CN",
            "+81": "JP",
            "+49": "DE",
            "+33": "FR",
            "+39": "IT",
            "+34": "ES",
            "+61": "AU",
            "+96": "AED",
            "+966": "SA",  # Saudi Arabia
        }
        default_country = country_code_map.get(default_country_code_with_plus, "IN")

        parsed = None

        # Strategy 1: Try adding + prefix and parsing as international number
        # This handles cases like 966536371512 (Saudi) or 919876543210 (India)
        if not v.startswith('+'):
            try:
                parsed = phonenumbers.parse(f'+{v}', None)
                if phonenumbers.is_valid_number(parsed):
                    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            except phonenumbers.NumberParseException:
                pass  # Try next strategy

        # Strategy 2: Try parsing as-is with None region (for numbers with + prefix)
        try:
            parsed = phonenumbers.parse(v, None)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            pass  # Try next strategy

        # Strategy 3: Try parsing with default country region
        # This works for local numbers like 9876543210 (India) or 2025551234 (if default is US)
        try:
            parsed = phonenumbers.parse(v, default_country)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            pass

        # If all strategies fail, raise error
        raise ValueError(f"Invalid phone number format: {v}")


def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize phone numbers for consistent comparisons (bypass checks).

    Ensures the number contains only digits and a leading + sign.
    """
    if not phone_number:
        return None

    try:
        # Validate and format using Pydantic model
        model = PhoneNumberModel(number=phone_number)
        return model.number
    except ValidationError as e:
        print_log(f"Invalid phone number '{phone_number}': {e}")
        raise ValueError(f"Invalid phone number: {phone_number}") from e


@lru_cache(maxsize=1)
def _load_bypass_numbers() -> set[str]:
    """
    Load the set of phone numbers that bypass business-hour validation.

    Numbers are read from the BUSINESS_HOURS_BYPASS_NUMBERS env var
    (comma-separated list). Normalization is applied before caching.
    """
    raw_numbers = os.getenv("BUSINESS_HOURS_BYPASS_NUMBERS", "")
    bypass_numbers: set[str] = set()

    for entry in raw_numbers.split(","):
        normalized = normalize_phone_number(entry.strip())
        if normalized:
            bypass_numbers.add(normalized)

    return bypass_numbers


def extract_country_code(phone_number: str) -> Optional[str]:
    """
    Extract country code from phone number.

    Args:
        phone_number: Phone number string (e.g., "+919876543210", "919876543210")

    Returns:
        Country code with + prefix (e.g., "+91") or None if not found

    Examples:
        >>> extract_country_code("+919876543210")
        '+91'
        >>> extract_country_code("966501234567")
        '+966'
        >>> extract_country_code("+12125551234")
        '+1'
    """
    if not phone_number:
        return None

    cleaned = normalize_phone_number(phone_number)
    if not cleaned:
        return None

    # Try to match known country codes (order matters - check longer codes first)
    for country_code in sorted(COUNTRY_TIMEZONE_MAP.keys(), key=len, reverse=True):
        if cleaned.startswith(country_code):
            return country_code

    # Fallback: extract first 1-3 digits after +
    match = re.match(r'\+(\d{1,3})', cleaned)
    if match:
        return f"+{match.group(1)}"

    return None


def get_timezone_for_phone(phone_number: str) -> Optional[str]:
    """
    Get timezone for a phone number based on its country code.

    Args:
        phone_number: Phone number string with country code

    Returns:
        Timezone name (e.g., "Asia/Kolkata") or None if not mapped

    Examples:
        >>> get_timezone_for_phone("+919876543210")
        'Asia/Kolkata'
        >>> get_timezone_for_phone("+966501234567")
        'Asia/Riyadh'
        >>> get_timezone_for_phone("+12125551234")
        'America/New_York'
    """
    country_code = extract_country_code(phone_number)
    if not country_code:
        print_log(
            f"Could not extract country code from phone number: {phone_number}",
            "timezone_utils_no_country_code"
        )
        return None

    timezone = COUNTRY_TIMEZONE_MAP.get(country_code)
    if not timezone:
        print_log(
            f"No timezone mapping for country code: {country_code}",
            "timezone_utils_no_mapping"
        )
        return None

    return timezone


def get_current_time_in_timezone(timezone_name: str) -> Optional[datetime]:
    """
    Get current time in specified timezone.

    Args:
        timezone_name: Timezone name (e.g., "Asia/Kolkata")

    Returns:
        Current datetime in specified timezone or None if timezone invalid
    """
    try:
        tz = pytz.timezone(timezone_name)
        return datetime.now(tz)
    except pytz.exceptions.UnknownTimeZoneError:
        print_log(
            f"Unknown timezone: {timezone_name}",
            "timezone_utils_unknown_timezone"
        )
        return None


def is_within_business_hours(
    phone_number: str,
    start_hour: int = 9,
    end_hour: int = 20
) -> Tuple[bool, Optional[datetime]]:
    """
    Check if current time is within business hours for the phone number's timezone.

    Business hours are defined as start_hour AM to end_hour (e.g., 9 AM to 8 PM).
    This function does NOT check weekends - calls are allowed 7 days a week.

    Args:
        phone_number: Phone number with country code
        start_hour: Business hours start (default: 9 for 9 AM)
        end_hour: Business hours end (default: 20 for 8 PM)

    Returns:
        Tuple of (is_within_hours, next_business_hour_utc)
        - is_within_hours: True if within business hours, False otherwise
        - next_business_hour_utc: If False, the next business hour in UTC; None if True

    Examples:
        >>> is_within_business_hours("+919876543210")  # Assuming it's 10 AM IST
        (True, None)
        >>> is_within_business_hours("+919876543210")  # Assuming it's 11 PM IST
        (False, datetime(...))  # Next day 9 AM IST in UTC
    """
    normalized_phone = normalize_phone_number(phone_number)
    bypass_numbers = _load_bypass_numbers()

    if normalized_phone in bypass_numbers:
        print_log(
            f"Bypassing business hours check for test number {normalized_phone}",
            "timezone_utils_bypass_number"
        )
        return True, None

    # Get timezone for phone number
    timezone_name = get_timezone_for_phone(normalized_phone)
    if not timezone_name:
        # If we can't determine timezone, allow the call (fail open)
        print_log(
            f"Could not determine timezone for {normalized_phone}, allowing call",
            "timezone_utils_allow_unknown"
        )
        return True, None

    # Get current time in recipient's timezone
    current_time = get_current_time_in_timezone(timezone_name)
    if not current_time:
        # If timezone lookup fails, allow the call (fail open)
        return True, None

    current_hour = current_time.hour

    # Check if within business hours
    if start_hour <= current_hour < end_hour:
        print_log(
            f"Phone {normalized_phone} within business hours. Current time in {timezone_name}: {current_time.strftime('%H:%M')}",
            "timezone_utils_within_hours"
        )
        return True, None

    # Calculate next business hour
    next_business_hour = calculate_next_business_hour(normalized_phone, start_hour)

    print_log(
        f"Phone {normalized_phone} outside business hours. Current time in {timezone_name}: {current_time.strftime('%H:%M')}. "
        f"Next business hour: {next_business_hour.strftime('%Y-%m-%d %H:%M %Z') if next_business_hour else 'unknown'}",
        "timezone_utils_outside_hours"
    )

    return False, next_business_hour


def calculate_next_business_hour(phone_number: str, start_hour: int = 9) -> Optional[datetime]:
    """
    Calculate the next business hour (start_hour AM) for a phone number's timezone.

    If current time is before start_hour AM today, returns today's start_hour AM.
    Otherwise returns tomorrow's start_hour AM.

    Args:
        phone_number: Phone number with country code
        start_hour: Business hours start (default: 9 for 9 AM)

    Returns:
        Next business hour as UTC datetime, or None if timezone cannot be determined

    Examples:
        >>> calculate_next_business_hour("+919876543210")  # If it's 11 PM IST
        datetime(...)  # Tomorrow 9 AM IST converted to UTC
    """
    # Get timezone for phone number
    timezone_name = get_timezone_for_phone(phone_number)
    if not timezone_name:
        return None

    # Get current time in recipient's timezone
    try:
        tz = pytz.timezone(timezone_name)
        current_time = datetime.now(tz)
    except pytz.exceptions.UnknownTimeZoneError:
        return None

    # Calculate next business hour in recipient's timezone
    next_business_time = current_time.replace(
        hour=start_hour,
        minute=0,
        second=0,
        microsecond=0
    )

    # If we're past business start time today, move to tomorrow
    if current_time.hour >= start_hour:
        next_business_time += timedelta(days=1)

    # Convert to UTC for storage
    utc_time = next_business_time.astimezone(pytz.UTC)

    return utc_time


def format_timezone_info(phone_number: str) -> str:
    """
    Format timezone information for logging/debugging.

    Args:
        phone_number: Phone number with country code

    Returns:
        Formatted string with timezone info
    """
    country_code = extract_country_code(phone_number)
    timezone_name = get_timezone_for_phone(phone_number)

    if not timezone_name:
        return f"Phone: {phone_number}, Country Code: {country_code or 'unknown'}, Timezone: not mapped"

    current_time = get_current_time_in_timezone(timezone_name)
    if not current_time:
        return f"Phone: {phone_number}, Country Code: {country_code}, Timezone: {timezone_name} (error getting time)"

    return (
        f"Phone: {phone_number}, "
        f"Country: {country_code}, "
        f"Timezone: {timezone_name}, "
        f"Local Time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    )
