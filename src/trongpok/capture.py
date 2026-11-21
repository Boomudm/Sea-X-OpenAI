"""Map captured marketplace fields to the rules' stable input keys."""

from .errors import ReaderInputError
from .profiles import CategoryProfile


def normalize_marketplace_fields(listing: dict, profile: CategoryProfile) -> dict:
    """Accept canonical captures and reject multiple values for the same field."""
    fields = profile.marketplace_fields
    groups = {
        "options": {
            "variation_label": fields.variation,
            "was_thb": fields.was_price,
            "now_thb": fields.now_price,
        },
        "reviews": {
            "variation_label": fields.variation,
            "buyer_masked": fields.buyer,
            "text": fields.review_text,
        },
    }
    normalized = dict(listing)
    for group, keys in groups.items():
        records = []
        for record in listing.get(group, ()):
            updated = dict(record)
            for canonical, source in keys.items():
                if source == canonical or source not in record:
                    continue
                if canonical in record and record[canonical] != record[source]:
                    raise ReaderInputError(f"Conflicting marketplace field for {group}.{canonical}")
                updated[canonical] = record[source]
                updated.pop(source)
            records.append(updated)
        normalized[group] = records
    return normalized
