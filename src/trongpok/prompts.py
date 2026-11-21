"""Versioned prompts. Changing one requires a cache-version bump."""

CLAIMS_PROMPT_VERSION = "extract_claims.v1"
REVIEWS_PROMPT_VERSION = "read_reviews.v1"
IMAGES_PROMPT_VERSION = "read_images.v1"
CONFIDENCE_PROMPT_VERSION = "assess_confidence.v1"

CLAIMS_DEVELOPER = """You extract storage capacity claims from captured listing options.
Use only the supplied text. One TB is 1,000 GB. Return one row for every supplied option.
Set capacity_unclear when capacity is missing, ambiguous, or conflicts with the listing title.
Do not infer a capacity from price or general product knowledge."""

REVIEWS_DEVELOPER = """You read captured buyer review text into checkable findings.
Return exactly one finding per supplied review. Copy an exact, contiguous quote from that
review. Extract a written number even when it is bare (for example 58), and inherit the
option's capacity unit for a bare capacity number. Roles are semantic: delivered capacity,
fails after, OS-reported, test result, promise, free space, speed, or other. Do not perform
the 85% decision; code validates the number and calculates it. Never invent text or values."""

IMAGES_DEVELOPER = """You classify captured storage evidence images. Classify each as OS
Properties, completed H2testw/F3, speed test, packaging/model code, or other. Extract a
visible quantity and unit only when readable. OS Properties is OS-reported, a completed
H2testw/F3 capacity is a test result, and speed tests are speed. Use cannot_read when the
image cannot be read. Never guess missing digits."""

CONFIDENCE_DEVELOPER = """Challenge a review-priority flag for one round without tools.
Consider GB vs GiB, wrong option, flash sale, duplicate buyer, or another concrete issue.
Every challenge must cite either an exact quote present in the supplied evidence or an
existing source identifier from that evidence. Do not change the flag colour or score."""
