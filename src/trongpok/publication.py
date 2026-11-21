"""Apply reviewer-facing wording and identity rules at publication boundaries."""

import hashlib
import re
from datetime import datetime

_RESTRICTED_WORD = re.compile(r"\b(?:fake|fraud)\w*", re.IGNORECASE)
_MASKED_BUYER = re.compile(r"[\w]?\*{2,}[\w]?|buyer-[0-9a-f]{12}\*{3}")
_DISPLAY_TEXT = {"capacity_text", "measurement_text", "quote", "reason", "reasons", "missing_evidence"}


def public_text(text: str) -> str:
    return _RESTRICTED_WORD.sub("[word omitted]", text)


def masked_buyer(buyer: str) -> str:
    buyer = buyer.strip()
    if not buyer or _MASKED_BUYER.fullmatch(buyer):
        return buyer
    digest = hashlib.sha256(buyer.encode("utf-8")).hexdigest()[:12]
    return f"buyer-{digest}***"


def publish_flag(flag: dict) -> dict:
    """Return a display copy after matching and confidence use the original evidence."""
    def sanitize(value, key=None):
        if isinstance(value, dict):
            return {name: sanitize(item, name) for name, item in value.items()}
        if isinstance(value, list):
            return [sanitize(item, key) for item in value]
        if isinstance(value, str):
            if key == "date":
                try:
                    datetime.fromisoformat(value)
                except ValueError:
                    return None
            if key == "buyer_masked":
                return masked_buyer(value)
            if key in _DISPLAY_TEXT:
                return public_text(value)
        return value

    return sanitize(flag)
