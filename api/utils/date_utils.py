from __future__ import annotations

from datetime import datetime

from pytz import timezone as pytz_timezone


IST = pytz_timezone("Asia/Kolkata")


def month_key_from_date_str(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%d-%m-%Y")
    except Exception:
        dt = datetime.now(IST)
    return dt.strftime("%Y-%m")


def current_month_key() -> str:
    return datetime.now(IST).strftime("%Y-%m")


def current_ist_date_str() -> str:
    return datetime.now(IST).strftime("%d-%m-%Y")
