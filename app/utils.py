import hashlib
from datetime import datetime, timedelta, timezone

def hash_url(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()

def compute_expiry(value, unit):
    if value is None or unit is None:
        return None

    now = datetime.now(timezone.utc)

    if unit == "minutes":
        return now + timedelta(minutes=value)
    if unit == "hours":
        return now + timedelta(hours=value)
    if unit == "days":
        return now + timedelta(days=value)
    if unit == "months":
        return now + timedelta(days=value * 30)

    raise ValueError("Invalid ttl_unit")

def ensure_utc(dt):
    if dt and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt