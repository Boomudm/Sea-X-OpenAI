from trongpok.profiles import load_profile
from trongpok.rules import build_option_flag, rescore_option_flag


def test_pipeline_rescore_retains_citations_and_does_not_change_flag_colour():
    profile = load_profile()
    option = {"option_id": "op", "variation_label": "64 GB", "promise_gb": 64}
    listing = {"listing_id": "listing", "options": [option], "reviews": []}
    base = build_option_flag(listing, option)
    accepted = {"kind": "other", "points": 10, "reason": "Check the dated capture", "source": "review:r1"}
    changes = [
        accepted,
        {**accepted, "reason": "Duplicate"},
        {**accepted, "source": "review:unknown"},
    ]

    result = rescore_option_flag(base, changes, eligible_sources={"review:r1"}, profile=profile)

    assert result["colour"] == base["colour"]
    assert result["confidence"]["score"] == base["confidence"]["score"] + 10
    assert result["confidence"]["adjustments"][-1] == {
        "points": 10, "reason": "Check the dated capture", "source": "review:r1",
    }
    assert len(result["confidence"]["adjustments"]) == len(base["confidence"]["adjustments"]) + 1
