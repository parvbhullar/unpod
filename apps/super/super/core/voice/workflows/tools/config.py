"""Centralized timezone and datetime utility for the post-call pipeline."""

import os
from datetime import datetime
from typing import Optional

import pytz

DEFAULT_TZ = "Asia/Kolkata"  # UTC+5:30


def get_timezone(model_config: Optional[dict] = None) -> pytz.BaseTzInfo:
    """Get timezone from model_config, env var, or default (Asia/Kolkata).

    Priority: model_config["timezone"] > env DEFAULT_TIMEZONE > Asia/Kolkata
    """
    tz_name = (
        (model_config or {}).get("timezone")
        or os.getenv("DEFAULT_TIMEZONE")
        or DEFAULT_TZ
    )
    return pytz.timezone(tz_name)


def get_now(model_config: Optional[dict] = None) -> datetime:
    """Return timezone-aware current datetime."""
    tz = get_timezone(model_config)
    return datetime.now(tz)
