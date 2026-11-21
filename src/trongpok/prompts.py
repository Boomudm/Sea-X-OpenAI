"""Versioned prompts. Changing one requires a cache-version bump."""

from .profiles import CategoryProfile, load_profile

CLAIMS_PROMPT_VERSION = "extract_claims.v1"
REVIEWS_PROMPT_VERSION = "read_reviews.v1"
IMAGES_PROMPT_VERSION = "read_images.v1"
CONFIDENCE_PROMPT_VERSION = "assess_confidence.v1"

CLAIMS_DEVELOPER = """You extract storage capacity claims from captured listing options.
Use only the supplied text. One TB is 1,000 GB. Return one row for every supplied option.
Set capacity_unclear when capacity is missing, ambiguous, or conflicts with the listing title.
Do not infer a capacity from price or general product knowledge."""

IMAGES_DEVELOPER = """You classify captured storage evidence images. Classify each as OS
Properties, completed H2testw/F3, speed test, packaging/model code, or other. Extract a
visible quantity and unit only when readable. OS Properties is OS-reported, a completed
H2testw/F3 capacity is a test result, and speed tests are speed. Use cannot_read when the
image cannot be read. Never guess missing digits."""

_REVIEW_OPENING = """You read captured buyer review text into checkable findings.
Return exactly one finding per supplied review. Copy an exact, contiguous quote from that"""
_CONFIDENCE_OPENING = "Challenge a review-priority flag for one round without tools."
_CONFIDENCE_SOURCES = """Every challenge must cite either an exact quote present in the supplied evidence or an
existing source identifier from that evidence. Do not change the flag colour or score."""
_GENERAL_CHALLENGES = "wrong option, flash sale, duplicate buyer, or another concrete issue."


def _role_label(role: str) -> str:
    return "OS-reported" if role == "os_reported" else role.replace("_", " ")


def _measurement_context(profile: CategoryProfile) -> str:
    languages = ", ".join(profile.languages)
    context = [
        f"Attribute: {profile.attribute}. Locale: {profile.locale}. Review languages: {languages}."
    ]
    if profile.measurement_mode == "numeric":
        units = ", ".join(
            f"{name} (aliases: {', '.join(conversion.all_aliases)})"
            if conversion.all_aliases else name
            for name, conversion in profile.units.items()
        )
        roles = ", ".join(map(_role_label, profile.measured_roles))
        context.extend((
            f"Accepted units: {units}. Advertised values use {profile.promise_unit}.",
            f"Measurement roles: {roles}.",
        ))
    else:
        context.append("Evaluate the reported mismatch type. This category uses no quantitative measurements.")
    context.append(f"Normal reading: {profile.normal_display_text}")
    traps = [
        *profile.prompt_traps,
        *(f"[{language}] {trap}"
          for language, entries in profile.prompt_traps_by_language.items() for trap in entries),
    ]
    if traps:
        context.append("Measurement pitfalls:" + "".join(f"\n- {trap}" for trap in traps))
    return "\n".join(context)



def review_developer(profile: CategoryProfile | None = None) -> str:
    """Build a review prompt while retaining the versioned storage wording."""
    profile = profile or load_profile()
    roles = list(map(_role_label, profile.review_roles))
    if profile.category == "storage":
        role_text = roles[0]
        if len(roles) > 1:
            remaining = ", ".join([*roles[1:-1], f"or {roles[-1]}"])
            role_text += f",\n{remaining}"
        percent = format((profile.tolerance * 100).normalize(), "f")
        return f"""{_REVIEW_OPENING}
review. Extract a written number even when it is bare (for example 58), and inherit the
option's {profile.attribute} unit for a bare {profile.attribute} number. Roles are semantic: {role_text}. Do not perform
the {percent}% decision; code validates the number and calculates it. Never invent text or values."""
    if profile.measurement_mode == "numeric":
        guidance = (
            "Extract a written number and its unit. A measurement requires an explicit,\n"
            "supported unit. If a complaint has no usable measurement, record it without a number."
        )
    else:
        guidance = "Classify the reported mismatch and leave the numeric fields empty."
    return f"""{_REVIEW_OPENING}
review. {guidance}
Allowed roles: {", ".join(roles)}.
Allowed mismatch types: {", ".join(profile.mismatch_types)}.
{_measurement_context(profile)}
Code validates the number and applies the tolerance. Never invent text or values."""


def confidence_developer(profile: CategoryProfile | None = None) -> str:
    """Build a one-round challenge prompt using the category's measurement context."""
    profile = profile or load_profile()
    if profile.category == "storage":
        challenges = ", ".join((*profile.prompt_traps[:1], _GENERAL_CHALLENGES))
        return f"""{_CONFIDENCE_OPENING}
Consider {challenges}
{_CONFIDENCE_SOURCES}"""
    return f"""{_CONFIDENCE_OPENING}
Consider {_GENERAL_CHALLENGES}
{_measurement_context(profile)}
{_CONFIDENCE_SOURCES}"""


REVIEWS_DEVELOPER = review_developer()
CONFIDENCE_DEVELOPER = confidence_developer()
