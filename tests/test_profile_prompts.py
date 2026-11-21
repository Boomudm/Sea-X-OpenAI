from trongpok import prompts
from trongpok.profiles import load_profile


_STORAGE_REVIEW = """You read captured buyer review text into checkable findings.
Return exactly one finding per supplied review. Copy an exact, contiguous quote from that
review. Extract a written number even when it is bare (for example 58), and inherit the
option's capacity unit for a bare capacity number. Roles are semantic: delivered capacity,
fails after, OS-reported, test result, promise, free space, speed, or other. Do not perform
the 85% decision; code validates the number and calculates it. Never invent text or values."""
_STORAGE_CONFIDENCE = """Challenge a review-priority flag for one round without tools.
Consider GB vs GiB, wrong option, flash sale, duplicate buyer, or another concrete issue.
Every challenge must cite either an exact quote present in the supplied evidence or an
existing source identifier from that evidence. Do not change the flag colour or score."""


def test_storage_prompts_keep_their_exact_text():
    assert prompts.REVIEWS_DEVELOPER == prompts.review_developer() == _STORAGE_REVIEW
    assert prompts.CONFIDENCE_DEVELOPER == prompts.confidence_developer() == _STORAGE_CONFIDENCE


def test_power_bank_prompts_explain_what_counts_as_a_measurement():
    profile = load_profile("power_bank")
    review = prompts.review_developer(profile)
    confidence = prompts.confidence_developer(profile)
    for prompt in (review, confidence):
        assert "Advertised values use mAh." in prompt
        assert "Measurement roles: test result." in prompt
        assert "USB-tester discharge" in prompt
        assert "60–70%" in prompt
        assert "Comparing Wh with mAh requires a known voltage basis." in prompt
        assert "GB vs GiB" not in prompt
    assert "supported unit. If a complaint has no usable measurement" in review
    assert "Allowed roles: test result, promise, speed, other." in review
    assert "capacity_no_number" in review
    assert "Do not change the flag colour or score." in confidence
